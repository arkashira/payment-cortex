# Payment Cortex

Payment Cortex is a payment processing engine that accepts and validates SWIFT and SEPA messages.

## Features

* Accepts and validates SWIFT MT103 and SEPA Credit Transfer messages
* Routes transactions to the correct settlement network
* Persists audit logs with immutable data

## Usage

1. Create a `PaymentCortex` instance
2. Call the `process_message` method with a SWIFT or SEPA message
3. The method will return the result of the transaction processing

## Testing

Run the tests using `pytest`
