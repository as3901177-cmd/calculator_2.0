"""
Custom exceptions
"""


class DXFAnalyzerError(Exception):
    """Base exception for DXF Analyzer"""
    pass


class DXFParsingError(DXFAnalyzerError):
    """Error parsing DXF file"""
    pass


class CalculationError(DXFAnalyzerError):
    """Error calculating length"""
    pass


class GeometryError(DXFAnalyzerError):
    """Error in geometry operations"""
    pass


class NestingError(DXFAnalyzerError):
    """Error in nesting optimization"""
    pass


class VisualizationError(DXFAnalyzerError):
    """Error in visualization"""
    pass