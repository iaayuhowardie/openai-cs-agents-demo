"""Tool definitions for airline customer service agents.

Each tool corresponds to an action an agent can take on behalf of a customer,
such as looking up flight status, modifying seats, or processing refunds.
"""

from datetime import datetime, timedelta
from typing import Optional

from agents import RunContextWrapper, function_tool

from .context import AirlineAgentContext
from .demo_data import apply_itinerary_defaults


# ---------------------------------------------------------------------------
# Flight Information Tools
# ---------------------------------------------------------------------------

@function_tool
def get_flight_status(
    context: RunContextWrapper[AirlineAgentContext],
    flight_number: str,
) -> str:
    """Return the current status of a flight.

    Args:
        flight_number: The flight number to look up (e.g. "AA123").
    """
    ctx = context.context
    itinerary = ctx.itinerary

    if itinerary and itinerary.flight_number.upper() == flight_number.upper():
        status = itinerary.status or "On Time"
        departure = itinerary.departure_time or "N/A"
        arrival = itinerary.arrival_time or "N/A"
        return (
            f"Flight {flight_number}: {status}. "
            f"Departure: {departure}, Arrival: {arrival}."
        )

    # Fallback for flights not in the customer's itinerary
    return f"Flight {flight_number} is currently On Time. No delays reported."


@function_tool
def get_itinerary(
    context: RunContextWrapper[AirlineAgentContext],
) -> str:
    """Retrieve the full itinerary for the authenticated customer."""
    ctx = context.context
    if not ctx.itinerary:
        return "No itinerary found for this account."

    it = apply_itinerary_defaults(ctx.itinerary)
    lines = [
        f"Booking Reference : {it.confirmation_number}",
        f"Flight            : {it.flight_number}",
        f"Route             : {it.origin} → {it.destination}",
        f"Departure         : {it.departure_time}",
        f"Arrival           : {it.arrival_time}",
        f"Seat              : {it.seat} ({it.seat_class})",
        f"Status            : {it.status}",
    ]
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Seat Service Tools
# ---------------------------------------------------------------------------

@function_tool
def list_available_seats(
    context: RunContextWrapper[AirlineAgentContext],
    seat_class: Optional[str] = None,
) -> str:
    """List available seats on the customer's booked flight.

    Args:
        seat_class: Optional filter — 'economy', 'business', or 'first'.
    """
    # Demo data: return a static list of seats
    all_seats = {
        "economy": ["22A", "22B", "34C", "35D", "40F"],
        "business": ["5A", "5B", "6C"],
        "first": ["1A", "2B"],
    }

    if seat_class:
        key = seat_class.lower()
        seats = all_seats.get(key)
        if seats is None:
            return f"Unknown seat class '{seat_class}'. Choose economy, business, or first."
        return f"Available {key} seats: {', '.join(seats)}"

    result_parts = [
        f"{cls.capitalize()}: {', '.join(seats)}"
        for cls, seats in all_seats.items()
    ]
    return "Available seats — " + " | ".join(result_parts)


@function_tool
def change_seat(
    context: RunContextWrapper[AirlineAgentContext],
    new_seat: str,
) -> str:
    """Change the customer's seat assignment.

    Args:
        new_seat: The desired seat number (e.g. "14C").
    """
    ctx = context.context
    if not ctx.itinerary:
        return "Unable to change seat: no itinerary found."

    old_seat = ctx.itinerary.seat or "unassigned"
    ctx.itinerary.seat = new_seat.upper()
    return (
        f"Seat successfully changed from {old_seat} to {new_seat.upper()} "
        f"on flight {ctx.itinerary.flight_number}."
    )


# ---------------------------------------------------------------------------
# Booking & Cancellation Tools
# ---------------------------------------------------------------------------

@function_tool
def cancel_booking(
    context: RunContextWrapper[AirlineAgentContext],
) -> str:
    """Cancel the customer's current booking."""
    ctx = context.context
    if not ctx.itinerary:
        return "No active booking found to cancel."

    confirmation = ctx.itinerary.confirmation_number
    ctx.itinerary.status = "Cancelled"
    return (
        f"Booking {confirmation} has been cancelled. "
        "A confirmation email will be sent shortly."
    )


# ---------------------------------------------------------------------------
# Refunds & Compensation Tools
# ---------------------------------------------------------------------------

@function_tool
def request_refund(
    context: RunContextWrapper[AirlineAgentContext],
    reason: str,
) -> str:
    """Submit a refund request for the customer's booking.

    Args:
        reason: The reason for the refund request.
    """
    ctx = context.context
    if not ctx.itinerary:
        return "No booking found to refund."

    confirmation = ctx.itinerary.confirmation_number
    # In a real system this would create a support ticket / call a payments API
    return (
        f"Refund request submitted for booking {confirmation}. "
        f"Reason: {reason}. "
        "You will receive a decision within 5–7 business days."
    )


@function_tool
def get_compensation_options(
    context: RunContextWrapper[AirlineAgentContext],
) -> str:
    """Return available compensation options for a delayed or cancelled flight."""
    ctx = context.context
    if not ctx.itinerary:
        return "No booking found. Please provide your booking details."

    status = (ctx.itinerary.status or "").lower()
    if "cancel" in status or "delay" in status:
        return (
            "Based on your disrupted flight you are eligible for: "
            "(1) Full refund to original payment method, "
            "(2) Travel voucher worth 120% of ticket value, or "
            "(3) Rebooking on the next available flight at no extra charge."
        )
    return (
        "Your flight does not currently show a qualifying disruption. "
        "If you believe this is an error, please describe the issue and we will investigate."
    )
