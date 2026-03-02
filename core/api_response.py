
def success(data):
    return {
        "success": True,
        "data": data,
        "error": None
    }

def failure(message):
    return {
        "success": False,
        "data": None,
        "error": message
    }
