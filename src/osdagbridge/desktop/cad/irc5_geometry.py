class CrashBarrierGeometry:

    @staticmethod
    def get_geometry(barrier_type: str) -> dict:

        if barrier_type == "IRC 5 - High Containment RCC Crash Barrier":
            return {
                "type": "rcc",
                "total_height": 900.0,
                "top_width": 175.0,
                "bottom_width": 350.0,
                "base_vertical": 100.0,
                "mid_offset": 350.0,
            }

        elif barrier_type == "IRC 5 - RCC Crash Barrier":
            return {
                "type": "rcc",
                "total_height": 750.0,
                "top_width": 150.0,
                "bottom_width": 300.0,
                "base_vertical": 100.0,
                "mid_offset": 300.0,
            }

        elif barrier_type == "IRC 5 - Metallic Crash Barrier with Single W-Beam":
            return {
                "type": "metallic",
                "w_beams": 1,
                "post_height": 950.0,
                "kerb_height": 150.0,
            }

        elif barrier_type == "IRC 5 - Metallic Crash Barrier with Double W-Beam":
            return {
                "type": "metallic",
                "w_beams": 2,
                "post_height": 950.0,
                "kerb_height": 150.0,
            }

        return {}
 
        
class RailingGeometry:

    @staticmethod
    def get_geometry(railing_type: str) -> dict:

        if railing_type == "IRC 5 - RCC Railing":
            return {
                "type": "rcc",
                "height": 1100,
                "width": 275,
                "post_spacing": 2000,
            }

        elif railing_type == "IRC 5 - Steel Railing":
            return {
                "type": "steel",
                "height": 1100,
                "post_dia": 50,
                "rail_count": 3,
                "post_spacing": 2000,
            }

        return {}
    
    
class MedianGeometry:

    @staticmethod
    def get_geometry(median_type: str) -> dict:

        if median_type == "IRC 5 - Raised Kerb":
            return {
                "type": "kerb",
                "median_width": 1200,
                "kerb_height": 225,
                "kerb_top_width": 1150,
                "kerb_bottom_width": 1200,
            }

        elif median_type == "IRC 5 - RCC Crash Barrier":
            return {
                "type": "rcc_barrier",
                "median_width": 1200,
                "barrier_height": 900,
                "top_width": 175,
                "bottom_width": 450,
            }

        elif median_type == "IRC 5 - Metallic Crash Barrier with Single W-Beam":
            return {
                "type": "metallic",
                "median_width": 1200,
                "post_height": 950,
                "w_beams": 1,
            }

        elif median_type == "IRC 5 - Metallic Crash Barrier with Double W-Beam":
            return {
                "type": "metallic",
                "median_width": 1200,
                "post_height": 950,
                "w_beams": 2,
            }

        return {}