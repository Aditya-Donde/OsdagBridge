"""
Export Handler for Plate Girder IFC
Connects the UI export button directly to the ifc_export_bridge engine.
Runs as an isolated background task.
"""
import sys
import threading
from osdagbridge.core.ifc_export_bridge.bridge_cad_extraction import PlateGirderIFCExtractor
from osdagbridge.core.ifc_export_bridge.bridge_ifc_generator import BridgeIfcGenerator

class PlateGirderIfcExportHandler:
    """Handles the extraction and generation lifecycle of the IFC file without blocking GUI."""
    
    def __init__(self, cad_generator, filepath, completion_callback=None):
        self.cad_generator = cad_generator
        self.filepath = filepath
        self.callback = completion_callback
        
    def export(self):
        """Extracts and Maps synchronously."""
        try:
            extractor = PlateGirderIFCExtractor(self.cad_generator)
            extracted_dict = extractor.extract()
            
            generator = BridgeIfcGenerator(self.filepath)
            generator.generate_from_extracted_data(extracted_dict, self.cad_generator)
            
            if self.callback:
                self.callback(True, f"Model successfully exported to {self.filepath}")
        except Exception as e:
            import traceback
            error_msg = traceback.format_exc()
            with open(r"c:\Users\Pyramid\Desktop\OsdagBridgeDev\OsdagBridge\src\osdagbridge\core\ifc_export_bridge\ifc_export_error.txt", "w") as f:
                f.write(error_msg)
            if self.callback:
                self.callback(False, str(e))
                
    def export_async(self):
        """Triggers export in a background thread to keep the Qt UI responsive."""
        thread = threading.Thread(target=self.export)
        thread.daemon = True
        thread.start()
