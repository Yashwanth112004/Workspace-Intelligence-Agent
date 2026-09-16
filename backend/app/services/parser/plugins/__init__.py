from app.services.parser.plugins.python_parser import PythonParserPlugin
from app.services.parser.plugins.typescript_parser import TypeScriptParserPlugin
from app.services.parser.plugins.go_parser import GoParserPlugin
from app.services.parser.plugins.c_family_parser import RustParserPlugin, CFamilyParserPlugin

ALL_PARSER_PLUGINS = [
    PythonParserPlugin(),
    TypeScriptParserPlugin(),
    GoParserPlugin(),
    RustParserPlugin(),
    CFamilyParserPlugin()
]
