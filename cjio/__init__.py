__version__ = "0.10.1"
import importlib.util


loader = importlib.util.find_spec("triangle")
MODULE_TRIANGLE_AVAILABLE = loader is not None

loader = importlib.util.find_spec("mapbox_earcut")
MODULE_EARCUT_AVAILABLE = loader is not None

loader = importlib.util.find_spec("pyproj")
MODULE_PYPROJ_AVAILABLE = loader is not None

loader = importlib.util.find_spec("pandas")
MODULE_PANDAS_AVAILABLE = loader is not None

loader = importlib.util.find_spec("cjvalpy")
MODULE_CJVAL_AVAILABLE = loader is not None
