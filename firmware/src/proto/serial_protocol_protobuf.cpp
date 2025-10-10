#include "serial_protocol_protobuf.h"
#include <string.h>
#include "semaphore_guard.h"

static SerialProtocolProtobuf *singleton_for_packet_serial = 0;

SerialProtocolProtobuf::SerialProtocolProtobuf(Stream &stream) : SerialProtocol(stream)
{
    packet_serial_.setStream(&stream);

    // Note: not threadsafe or instance safe!! but PacketSerial requires a legacy function pointer, so we can't
    // use a member, std::function, or lambda with captures
    assert(singleton_for_packet_serial == 0);
    singleton_for_packet_serial = this;

    packet_serial_.setPacketHandler([](const uint8_t *buffer, size_t size)
                                    { singleton_for_packet_serial->handlePacket(buffer, size); });

    // Initialize TX mutex to serialize protobuf encoding and PacketSerial sends across tasks
    tx_mutex_ = xSemaphoreCreateMutex();
    assert(tx_mutex_ != NULL);
}

SerialProtocolProtobuf::~SerialProtocolProtobuf()
{
    if (tx_mutex_ != NULL)
    {
        vSemaphoreDelete(tx_mutex_);
        tx_mutex_ = NULL;
    }
}

void SerialProtocolProtobuf::log(const LogMessage &log_msg)
{
    // Serialize fill + send to avoid union races across tasks
    SemaphoreGuard lock(tx_mutex_);
    pb_tx_buffer_ = {};
    pb_tx_buffer_.which_payload = PB_FromSmartKnob_log_tag;
    pb_tx_buffer_.payload.log.level = LogLevelConverter::toPBLogLevel(log_msg.level);
    pb_tx_buffer_.payload.log.isVerbose = log_msg.verbose;

    strlcpy(pb_tx_buffer_.payload.log.origin, log_msg.origin, sizeof(pb_tx_buffer_.payload.log.origin));
    strlcpy(pb_tx_buffer_.payload.log.msg, log_msg.msg, sizeof(pb_tx_buffer_.payload.log.msg));
    // TODO add timestamp

    sendPBTxBufferLocked_();
}

void SerialProtocolProtobuf::log_raw(const char *msg)
{
    // Avoid LOG* here to prevent re-entrant logging deadlocks while tx path may hold tx_mutex_
    // Emit a minimal diagnostic on the underlying stream separated from COBS packets.
    stream_.print("[RAW] ");
    stream_.println(msg ? msg : "(null)");
    stream_.flush();
}

void SerialProtocolProtobuf::registerTagCallback(pb_size_t tag, TagCallback callback)
{
    tag_callbacks_[tag] = callback;
}

void SerialProtocolProtobuf::registerCommandCallback(PB_SmartKnobCommand command, CommandCallback callback)
{
    command_callbacks_[command] = callback;
}

void SerialProtocolProtobuf::sendKnobInfo(PB_Knob knob)
{
    // Serialize fill + send to avoid union races across tasks
    SemaphoreGuard lock(tx_mutex_);
    pb_tx_buffer_ = {};
    pb_tx_buffer_.which_payload = PB_FromSmartKnob_knob_tag;
    pb_tx_buffer_.payload.knob = knob;
    sendPBTxBufferLocked_();
}

void SerialProtocolProtobuf::sendKnobState(PB_SmartKnobState state)
{
    // Serialize fill + send to avoid union races across tasks
    SemaphoreGuard lock(tx_mutex_);
    pb_tx_buffer_ = {};
    pb_tx_buffer_.which_payload = PB_FromSmartKnob_smartknob_state_tag;
    pb_tx_buffer_.payload.smartknob_state = state;
    sendPBTxBufferLocked_();
}

void SerialProtocolProtobuf::handlePacket(const uint8_t *buffer, size_t size)
{
    // LOGI(" packet received!");
    if (size <= 4)
    {
        // Too small, ignore bad packet
        LOGD("Small packet received. Ignoring. size=%u", (unsigned)size);
        return;
    }

    // Compute and append little-endian CRC32
    uint32_t expected_crc = 0;
    crc32(buffer, size - 4, &expected_crc);

    uint32_t provided_crc = buffer[size - 4] | (buffer[size - 3] << 8) | (buffer[size - 2] << 16) | (buffer[size - 1] << 24);

    if (expected_crc != provided_crc)
    {
        LOGE("Bad CRC (%u byte packet). Expected %08x but got %08x.", size - 4, expected_crc, provided_crc);
        return;
    }
    else
    {
        // LOGI("CRC check passed");
    }

    pb_istream_t stream = pb_istream_from_buffer(buffer, size - 4);
    if (!pb_decode(&stream, PB_ToSmartknob_fields, &pb_rx_buffer_))
    {
        LOGE("Decoding failed: %s", PB_GET_ERROR(&stream));
        return;
    }
    else
    {
        // LOGI("Decoding successful, protocol version: %u", pb_rx_buffer_.protocol_version);
    }

    if (pb_rx_buffer_.protocol_version != PROTOBUF_PROTOCOL_VERSION)
    {
        LOGE("Invalid protocol version. Expected %u, received %u", PROTOBUF_PROTOCOL_VERSION, pb_rx_buffer_.protocol_version);
        return;
    }

    // Always ACK immediately
    ack(pb_rx_buffer_.nonce);
    if (pb_rx_buffer_.nonce == last_nonce_)
    {
        LOGD("Already handled nonce %u", pb_rx_buffer_.nonce);
        return;
    }
    else
    {
        // LOGI("New nonce received: %u", pb_rx_buffer_.nonce);
    }
    last_nonce_ = pb_rx_buffer_.nonce;

    // Verbose diagnostics: log payload tag and key fields
    LOGI("SerialProtocolProtobuf: RX nonce=%u payload_tag=%d size=%u",
         pb_rx_buffer_.nonce, (int)pb_rx_buffer_.which_payload, (unsigned)size);

    if (pb_rx_buffer_.which_payload == PB_ToSmartknob_app_component_tag)
    {
        const PB_AppComponent &ac = pb_rx_buffer_.payload.app_component;
        int details = (ac.which_component_config == PB_AppComponent_multi_choice_tag)
                          ? (int)ac.component_config.multi_choice.options_count
                          : -1;

        // SAFETY: nanopb char arrays may not be null-terminated; make a bounded, explicitly terminated copy.
        size_t id_len = strnlen(ac.component_id, sizeof(ac.component_id));
        char id_buf[sizeof(ac.component_id) + 1];
        memcpy(id_buf, ac.component_id, id_len);
        id_buf[id_len] = '\0';

        LOGI("SerialProtocolProtobuf: AppComponent id='%s' type=%d which=%d options_count=%d",
             id_buf, (int)ac.type, (int)ac.which_component_config, details);
    }

    // todo: what is the difference between a tag callback and a button command?
    // LOGI("Searching for tag callback");
    if (tag_callbacks_.find(pb_rx_buffer_.which_payload) != tag_callbacks_.end())
    {
        // LOGI("tag callback found, creating task");
        TagHandlerParams *params = new TagHandlerParams{
            new std::function<void(const PB_ToSmartknob &)>(tag_callbacks_[pb_rx_buffer_.which_payload]),
            pb_rx_buffer_};

        //  LOGI("Task creation starting...");
        xTaskCreate(
            [](void *param)
            {
                TagHandlerParams *params = reinterpret_cast<TagHandlerParams *>(param);

                (*params->handler)(params->pb_rx_buffer_copy);

                delete params->handler;
                delete params;

                vTaskDelete(NULL);
            },
            "tag_handler_task", 1024 * 12, params, 5, NULL);
    }
    else if (pb_rx_buffer_.which_payload == PB_ToSmartknob_smartknob_command_tag)
    {
        // LOGI("=== COMMAND RECEIVED: %d ===", pb_rx_buffer_.payload.smartknob_command);
        if (command_callbacks_.find(pb_rx_buffer_.payload.smartknob_command) != command_callbacks_.end())
        {
            // LOGI("Command callback found, creating task...");
            auto handler = new std::function<void()>(command_callbacks_[pb_rx_buffer_.payload.smartknob_command]);
            // LOGI("Task creation starting...");
            xTaskCreate(
                [](void *param)
                {
                    // LOGI("=== COMMAND TASK STARTED ===");
                    auto handler = reinterpret_cast<std::function<void()> *>(param);
                    // LOGI("About to execute command handler...");
                    (*handler)();
                    // LOGI("Command handler execution completed");
                    delete handler;
                    // LOGI("=== COMMAND TASK ENDING ===");
                    vTaskDelete(NULL);
                },
                "key_handler_task", 1024 * 10, handler, 5, NULL); // TODO stack size and priority?
            // LOGI("Task creation completed");
        }
        else
        {
            LOGE("Unknown command: %d", pb_rx_buffer_.payload.smartknob_command);
        }
    }
    else
    {
        LOGE("Unknown payload");
    }
}

void SerialProtocolProtobuf::sendPBTxBuffer()
{
    // Public wrapper: take the mutex then perform the encode/send
    SemaphoreGuard lock(tx_mutex_);
    sendPBTxBufferLocked_();
}

void SerialProtocolProtobuf::sendPBTxBufferLocked_()
{
    // Encode protobuf message to byte buffer (assumes tx_mutex_ is held)
    pb_ostream_t stream = pb_ostream_from_buffer(tx_buffer_, sizeof(tx_buffer_));
    pb_tx_buffer_.protocol_version = PROTOBUF_PROTOCOL_VERSION;

    stream.bytes_written = 0;
    if (!pb_encode(&stream, PB_FromSmartKnob_fields, &pb_tx_buffer_))
    {
        // Avoid LOGE here to prevent re-entrant protobuf logging while tx_mutex_ is held
        stream_.print("PB encode error: ");
        stream_.println(stream.errmsg);
        stream_.print("PB bytes written when failed: ");
        stream_.println((unsigned)stream.bytes_written);
        stream_.flush();
        return;
    }

    // Compute and append little-endian CRC32
    uint32_t crc = 0;
    crc32(tx_buffer_, stream.bytes_written, &crc);
    tx_buffer_[stream.bytes_written + 0] = (crc >> 0) & 0xFF;
    tx_buffer_[stream.bytes_written + 1] = (crc >> 8) & 0xFF;
    tx_buffer_[stream.bytes_written + 2] = (crc >> 16) & 0xFF;
    tx_buffer_[stream.bytes_written + 3] = (crc >> 24) & 0xFF;

    // Encode and send proto+CRC as a COBS packet
    packet_serial_.send(tx_buffer_, stream.bytes_written + 4);
    stream_.flush();
}

void SerialProtocolProtobuf::ack(uint32_t nonce)
{
    // Verbose ACK diagnostics to correlate with host-side ACK wait
    LOGI("SerialProtocolProtobuf: ACK sent nonce=%u", (unsigned)nonce);

    // Serialize fill + send to avoid union races across tasks
    SemaphoreGuard lock(tx_mutex_);
    pb_tx_buffer_ = {};
    pb_tx_buffer_.which_payload = PB_FromSmartKnob_ack_tag;
    pb_tx_buffer_.payload.ack.nonce = nonce;
    sendPBTxBufferLocked_();
}

void SerialProtocolProtobuf::readSerial()
{
    do
    {
        packet_serial_.update();
    } while (stream_.available());
}
