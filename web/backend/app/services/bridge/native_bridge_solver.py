from app.models.bridge import BridgeInput


def run_bridge_analysis(data: BridgeInput):

    # Safe span
    span = (
        data.span_length
        or data.span
        or 35000
    )

    # Safe width
    width = (
        data.carriageway_width
        or data.overall_bridge_width
        or data.width
        or 12000
    )

    # Safe girders
    girders = (
        data.no_of_girders
        or data.num_girders
        or 4
    )

    # Safe deck thickness
    deck_thickness = (
        data.deck_thickness
        or 200
    )

    # Dummy calculations
    max_moment = span * width * 10
    max_shear = span * 5
    max_displacement = span / 500

    return {
        "status": "success",

        "inputs": {
            "span": span,
            "width": width,
            "girders": girders,
            "deck_thickness": deck_thickness,
        },

        "maxMoment": round(max_moment, 2),
        "maxShear": round(max_shear, 2),
        "maxDisplacement": round(max_displacement, 4),
    }