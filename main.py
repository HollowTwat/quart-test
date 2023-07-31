
import asyncio, os
from quart import Quart, render_template
from quart_compress import Compress
from hypercorn.asyncio import serve
from hypercorn.config import Config


PORT =                  os.getenv('PORT')

app = Quart(__name__, static_url_path='/static')
Compress(app)


@app.errorhandler(404)
async def handle_not_found(e):
    return '<h1>😦</h1><b>404</b> Not found.<p><a href="/">return</a>'


@app.route("/")
async def index() -> str:
        return await render_template("index.html")


if __name__ == "__main__":

    app.run("0.0.0.0",PORT) # debug server for testing

    ### uncomment for production
    # config = Config()
    # config.bind = [f"0.0.0.0:{PORT}"]
    # asyncio.run(serve(app, config))