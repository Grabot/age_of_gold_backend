from flask import make_response


def get_failed_response(message):
    get_hexagon_response = make_response({
        'result': False,
        'message': message,
    }, 200)
    return get_hexagon_response

