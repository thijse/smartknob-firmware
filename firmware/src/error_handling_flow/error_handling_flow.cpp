#include "error_handling_flow.h"

ErrorHandlingFlow::ErrorHandlingFlow(SemaphoreHandle_t mutex) : mutex_(mutex)
{
    page_manager = new ErrorHandlingPageManager(lv_obj_create(NULL), mutex_);
}

void ErrorHandlingFlow::handleEvent(Event event)
{
    Event send_event;
    motor_notifier->requestUpdate(blocked_motor_config);

    ErrorPage *error_page = (ErrorPage *)page_manager->getPage(ErrorPages::ERROR_PAGE);
    ResetPage *reset_page = (ResetPage *)page_manager->getPage(ErrorPages::RESET_PAGE);

    error_type = NO_ERROR;

    switch (event.type)
    {
    case SK_RESET_BUTTON_PRESSED:
        error_type = ErrorType::RESET;
        break;
    case SK_RESET_BUTTON_RELEASED:
        // lv_timer_del(timer);
        //! DELETE TIMER ON RESET PAGE IN PAGE MANAGER??
    case SK_DISMISS_ERROR:
    case SK_RESET_ERROR:
        error_type = NO_ERROR;
        error_state = {
            NO_ERROR,
            {SK_NO_EVENT, {}, 0},
            1,
        };
        break;
    default:
        LOGE("UNKNOWN EVENT");
        break;
    }

    error_state.latest_error_type = error_type;
    error_state.latest_event = event;

    switch (error_type)
    {
    case RESET:
        reset_page->show();
        page_manager->render(ErrorPages::RESET_PAGE);
        break;
    case NO_ERROR: // DO NOTHING
        break;
    default:
        LOGE("UNKNOWN ERROR");
        break;
    }
}

void ErrorHandlingFlow::handleNavigationEvent(NavigationEvent event)
{
    Event send_event;
    send_event.body.error.type = error_type;

    switch (event)
    {
    case NavigationEvent::SHORT:
        send_event.type = SK_RESET_ERROR;
        break;
    case NavigationEvent::LONG:
        send_event.type = SK_DISMISS_ERROR;
        break;
    default:
        break;
    }
}

void ErrorHandlingFlow::setMotorNotifier(MotorNotifier *motor_notifier)
{
    this->motor_notifier = motor_notifier;
}

void ErrorHandlingFlow::setSharedEventsQueue(QueueHandle_t shared_events_queue)
{
    this->shared_events_queue = shared_events_queue;
}

void ErrorHandlingFlow::publishEvent(Event event)
{
    event.sent_at = millis();
    xQueueSendToBack(shared_events_queue, &event, 0);
}

ErrorType ErrorHandlingFlow::getErrorType()
{
    return error_type;
}
