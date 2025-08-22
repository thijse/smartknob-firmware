#pragma once

#include <stdint.h>

enum ErrorType
{
    NO_ERROR,
    RESET,
    ERROR_TYPE_COUNT
};

struct Error
{
    ErrorType type;
};

union EventBody
{
    Error error;
    uint8_t calibration_step;
};

enum EventType
{
    SK_RESET_ERROR = 1,
    SK_DISMISS_ERROR,

    SK_RESET_BUTTON_PRESSED,
    SK_RESET_BUTTON_RELEASED,

    SK_CONFIGURATION_SAVED,

    SK_SETTINGS_CHANGED,

    SK_STRAIN_CALIBRATION,

    SK_NO_EVENT
};

typedef unsigned long SentAt;

struct Event
{
    EventType type;
    EventBody body;
    SentAt sent_at;
};

struct ErrorState
{
    ErrorType latest_error_type;
    Event latest_event;
    uint8_t retry_count;
};
