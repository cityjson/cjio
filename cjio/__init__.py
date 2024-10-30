__version__ = "0.9.0"
import importlib

loader = importlib.find_loader("triangle")
MODULE_TRIANGLE_AVAILABLE = loader is not None

loader = importlib.find_loader("mapbox_earcut")
MODULE_EARCUT_AVAILABLE = loader is not None

loader = importlib.find_loader("pyproj")
MODULE_PYPROJ_AVAILABLE = loader is not None

loader = importlib.find_loader("pandas")
MODULE_PANDAS_AVAILABLE = loader is not None

loader = importlib.find_loader("cjvalpy")
MODULE_CJVAL_AVAILABLE = loader is not None
