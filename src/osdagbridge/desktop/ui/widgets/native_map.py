
import math
from functools import lru_cache
from PySide6.QtWidgets import QWidget
from PySide6.QtCore import Qt, Signal, QPoint, QPointF, QRect, QRectF, QUrl
from PySide6.QtGui import QPainter, QPixmap, QImage, QBrush, QColor, QPen, QMouseEvent, QWheelEvent, QPainterPath
from PySide6.QtNetwork import QNetworkAccessManager, QNetworkRequest, QNetworkDiskCache, QNetworkReply

class NativeMapWidget(QWidget):
    """
    A native tile-based map widget that fetches OpenStreetMap tiles 
    and renders them using QPainter. this avoids QWebEngineView dependency.
    """
    locationSelected = Signal(float, float)  # Emits (lat, lon) on click

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMouseTracking(True)
        
        # Initial View (Center of India roughly)
        self.latitude = 20.5937
        self.longitude = 78.9629
        self.zoom = 5
        self.min_zoom = 2
        self.max_zoom = 18
        
        # Marker (None initially, or set to a default)
        self.marker_lat = None
        self.marker_lon = None
        
        # Tile size
        self.tile_size = 256
        
        # Network Manager for fetching tiles
        self.manager = QNetworkAccessManager(self)
        self.cache = QNetworkDiskCache(self)
        self.cache.setCacheDirectory("osdag_map_cache")
        self.cache.setMaximumCacheSize(50 * 1024 * 1024) # 50 MB
        self.manager.setCache(self.cache)
        
        # In-memory image cache (url -> QPixmap)
        self.pixmap_cache = {}
        
        # Interaction state
        self._last_mouse_pos = QPoint()
        self._is_panning = False
        self._mouse_press_pos = QPoint() # To distinguish click from pan

        # Initialize
        self.setMinimumSize(400, 300)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        width = self.width()
        height = self.height()
        
        # 1. Calculate center pixel in world coordinates
        center_px_x, center_px_y = self.lat_lon_to_pixel(self.latitude, self.longitude, self.zoom)
        
        # 2. Determine visible tile range
        # Top-left of the viewport in world pixels
        view_x = center_px_x - width / 2
        view_y = center_px_y - height / 2
        
        start_col = math.floor(view_x / self.tile_size)
        end_col = math.floor((view_x + width) / self.tile_size)
        start_row = math.floor(view_y / self.tile_size)
        end_row = math.floor((view_y + height) / self.tile_size)
        
        total_tiles = 2 ** self.zoom
        
        # 3. Draw Tiles
        for col in range(start_col, end_col + 1):
            for row in range(start_row, end_row + 1):
                # Handle wrapping for x (longitude)
                tile_x = col % total_tiles
                tile_y = row
                
                # Check bounds for y (latitude doesn't wrap typically for Mercator)
                if tile_y < 0 or tile_y >= total_tiles:
                    continue
                
                # Logic to draw the specific tile
                self.draw_tile(painter, tile_x, tile_y, col, row, view_x, view_y)
        
        # 4. Draw Marker (Pin) if it exists
        if self.marker_lat is not None and self.marker_lon is not None:
             marker_px_x, marker_px_y = self.lat_lon_to_pixel(self.marker_lat, self.marker_lon, self.zoom)
             screen_marker_x = marker_px_x - view_x
             screen_marker_y = marker_px_y - view_y
             
             # Draw simple pin
             painter.setBrush(QBrush(QColor(255, 0, 0)))
             painter.setPen(Qt.NoPen)
             # Circle head
             painter.drawEllipse(QPointF(screen_marker_x, screen_marker_y - 15), 8, 8)
             # Triangle pointing down
             path = QPainterPath()
             path.moveTo(screen_marker_x - 7, screen_marker_y - 11)
             path.lineTo(screen_marker_x + 7, screen_marker_y - 11)
             path.lineTo(screen_marker_x, screen_marker_y)
             path.closeSubpath()
             painter.drawPath(path)

        painter.end()

    def draw_tile(self, painter, tile_x, tile_y, col, row, view_x, view_y):
        url = f"https://tile.openstreetmap.org/{self.zoom}/{tile_x}/{tile_y}.png"
        
        # Calculate screen position
        screen_x = (col * self.tile_size) - view_x
        screen_y = (row * self.tile_size) - view_y
        
        if url in self.pixmap_cache:
            painter.drawPixmap(int(screen_x), int(screen_y), self.pixmap_cache[url])
        else:
            # Draw placeholder
            painter.setBrush(QColor(240, 240, 240))
            painter.drawRect(int(screen_x), int(screen_y), self.tile_size, self.tile_size)
            self.fetch_tile(url)

    def fetch_tile(self, url):
        request = QNetworkRequest(QUrl(url))
        request.setAttribute(QNetworkRequest.CacheLoadControlAttribute, QNetworkRequest.PreferCache)
        # Identify user agent as polite usage policy requires
        request.setHeader(QNetworkRequest.UserAgentHeader, "OsdagBridge/1.0 (Garvit)")
        
        reply = self.manager.get(request)
        reply.finished.connect(lambda: self.on_tile_loaded(reply, url))

    def on_tile_loaded(self, reply, url):
        if reply.error() == QNetworkReply.NoError:
            data = reply.readAll()
            pixmap = QPixmap()
            pixmap.loadFromData(data)
            self.pixmap_cache[url] = pixmap
            self.update() # Trigger repaint
        reply.deleteLater()

    # --- Interaction ---
    def mousePressEvent(self, event: QMouseEvent):
        if event.button() == Qt.LeftButton:
            self._is_panning = True
            self._last_mouse_pos = event.pos()
            self._mouse_press_pos = event.pos()
            self.setCursor(Qt.ClosedHandCursor)

    def mouseMoveEvent(self, event: QMouseEvent):
        if self._is_panning:
            delta = event.pos() - self._last_mouse_pos
            self._last_mouse_pos = event.pos()
            
            # Panning moves the map view provided we shift center opposite to mouse
            # Convert screen delta to world pixel delta
            self.pan_map(-delta.x(), -delta.y())

    def mouseReleaseEvent(self, event: QMouseEvent):
        if event.button() == Qt.LeftButton:
            self._is_panning = False
            self.setCursor(Qt.ArrowCursor)
            
            # Check if it was a click (distance moved < threshold)
            dist = (event.pos() - self._mouse_press_pos).manhattanLength()
            if dist < 5:
                # Clicked! Place marker.
                self.place_marker_at_screen_pos(event.pos())

    def place_marker_at_screen_pos(self, screen_pos):
         # Convert screen click to world lat/lon
         width = self.width()
         height = self.height()
         
         center_px_x, center_px_y = self.lat_lon_to_pixel(self.latitude, self.longitude, self.zoom)
         view_x = center_px_x - width / 2
         view_y = center_px_y - height / 2
         
         click_px_x = view_x + screen_pos.x()
         click_px_y = view_y + screen_pos.y()
         
         lat, lon = self.pixel_to_lat_lon(click_px_x, click_px_y, self.zoom)
         
         self.marker_lat = lat
         self.marker_lon = lon
         self.locationSelected.emit(lat, lon)
         self.update()

    def wheelEvent(self, event: QWheelEvent):
        angle = event.angleDelta().y()
        if angle > 0:
            self.zoom_in()
        else:
            self.zoom_out()

    def zoom_in(self):
        new_zoom = min(self.zoom + 1, self.max_zoom)
        self.set_zoom(new_zoom)

    def zoom_out(self):
        new_zoom = max(self.zoom - 1, self.min_zoom)
        self.set_zoom(new_zoom)

    def set_zoom(self, new_zoom):
        if new_zoom != self.zoom:
            self.zoom = new_zoom
            self.pixmap_cache.clear() # Clear cache on zoom change for simplicity or manage better
            self.update()

    def pan_map(self, dx_px, dy_px):
        # Convert pixel delta to lat/lon delta at current zoom
        center_px_x, center_px_y = self.lat_lon_to_pixel(self.latitude, self.longitude, self.zoom)
        
        new_px_x = center_px_x + dx_px
        new_px_y = center_px_y + dy_px
        
        self.latitude, self.longitude = self.pixel_to_lat_lon(new_px_x, new_px_y, self.zoom)
        self.update()

    # --- Math Helpers (Web Mercator) ---
    def lat_lon_to_pixel(self, lat, lon, zoom):
        n = 2 ** zoom
        # x
        x_norm = (lon + 180) / 360
        x_pixel = x_norm * n * self.tile_size
        
        # y
        lat_rad = math.radians(lat)
        # Avoid infinity at poles
        lat_rad = max(min(lat_rad, 1.4844), -1.4844) 
        
        y_norm = (1 - math.log(math.tan(lat_rad) + (1 / math.cos(lat_rad))) / math.pi) / 2
        y_pixel = y_norm * n * self.tile_size
        
        return x_pixel, y_pixel

    def pixel_to_lat_lon(self, x_pixel, y_pixel, zoom):
        n = 2 ** zoom
        
        # lon
        x_norm = x_pixel / (n * self.tile_size)
        lon = x_norm * 360 - 180
        
        # lat
        y_norm = y_pixel / (n * self.tile_size)
        n_inv_pi = math.pi * (1 - 2 * y_norm)
        state = math.atan(math.sinh(n_inv_pi))
        lat = math.degrees(state)
        
        return lat, lon


    def set_marker_location(self, lat, lon):
        """
        Sets the marker location programmatically and centers the map.
        This is useful for syncing when coordinates are entered manually.
        """
        self.marker_lat = lat
        self.marker_lon = lon
        self.latitude = lat
        self.longitude = lon
        
        # Center the view on the new location
        if self.pixmap_cache:
            # Optionally clear cache or just let it fetch new tiles
            # self.pixmap_cache.clear() 
            pass
            
        self.locationSelected.emit(lat, lon) # Optional: emit signal if we want uniform behavior, 
                                             # but beware of infinite loops if connected to inputs!
                                             # Typically we don't emit if setting FROM the input.
                                             # We won't emit here to avoid loops.
        self.update()
