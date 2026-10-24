from fastmcp import FastMCP
mcp = FastMCP("calculator")

@mcp.tool
def add(a: int, b: int) -> int:
    """Add two numbers."""
    return a + b

@mcp.tool
def substract(a: int, b: int) -> int:
    """Subtract two numbers."""
    return a - b

if __name__ == "__main__":
    mcp.run()