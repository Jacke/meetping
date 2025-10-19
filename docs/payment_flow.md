# payment_bot - Flow Diagram

```mermaid
stateDiagram-v2
    [*] --> welcome
    welcome --> route_user: check passed (1s)
    welcome --> welcome: polling...
    note right of welcome
        Actions:\nreload_texts_and_config
    end note
    route_user --> already_paid: check passed (1s)
    route_user --> route_user: polling...
    show_welcome --> payment_info: click '💳 Оплатить билет на мероприятие'
    payment_pending --> awaiting_payment: auto
    already_paid --> [*]
    payment_info --> awaiting_payment: auto
    note right of payment_info
        Actions:\ncreate_payment_record
    end note
    awaiting_payment --> success: check passed (10s)
    awaiting_payment --> awaiting_payment: polling...
    success --> [*]
```
