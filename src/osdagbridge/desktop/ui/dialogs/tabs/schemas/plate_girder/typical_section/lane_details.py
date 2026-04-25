LANE_DETAILS_TAB_SCHEMA = {
    "id": "lane_details_tab",
    "rows": [
        {
            "fields": [
                {
                    "id": "lane_count",
                    "label": "No. of Traffic Lanes:",
                    "type": "combo",
                    "choices": [str(i) for i in range(1, 7)],
                    "bind": "lane_count_combo",
                    "on_change": "on_lane_count_changed",
                }
            ]
        }
    ],
}
