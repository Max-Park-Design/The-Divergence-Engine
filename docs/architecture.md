# Runtime organisation

`unblocker.py` owns shared hardware state and coordinates each run. It opens the
Arduino connection during module initialisation, loads the OLED frames and starts
background services near the end of the module. Importing it is therefore not a
read-only operation.

## Code navigation

| Area | Main functions |
| --- | --- |
| Persistent state | `save_state`, `load_state` |
| Serial hardware | `get_hardware_inputs`, `serial_reader_thread` |
| OLED displays | `_load_oled_frames`, `update_displays` |
| Pulse readings | `calc_hr_spo2_manual`, `read_emotional_state` |
| USB documents | `usb_monitor_thread`, `load_usb_pdfs`, `sample_across_text` |
| Receipt output | `send_print`, `print_raster_paced` |
| Editorial selection | `pick_topic`, `choose_country`, `get_allowed_source_types` |
| Source discovery | `find_sources_with_mistral`, `dedupe_and_rank_sources` |
| Evidence processing | `add_link_source`, `wait_for_source_processing`, `fetch_source_content` |
| Synthesis | `query_with_mistral_directly`, `_run_query` |
| Image selection | `generate_delta_topic`, `find_wikimedia_image` |
| Image preparation | `process_image_for_thermal` |
| Web output | `generate_html_summary`, `save_html_and_qr` |
| Run coordination | `build_notebook_for_topic`, `run_demo` |

The demo helper module validates local records, selects the nearest eligible
record and archives its assets. `add_demo.py` is a standalone import utility.

## Maintenance constraints

The controller uses mutable globals, background threads and initialisation at
module scope. Moving functions into another module changes which globals they
read and write unless ownership is explicitly preserved. Runtime extraction
needs hardware validation as well as static checks.

The controller currently defines `_run_query` and `sample_across_text` twice.
The later definitions replace the earlier bindings during normal initialisation.
Both definitions are retained in this source release to preserve the original
statement sequence and prompt text.
