# AVL Tree Studio

Interactive Flask web app to build and visualize an AVL (self-balancing BST) in real time.

## Run locally

1. Activate the virtual environment if needed.
2. Install dependencies from `requirements.txt`.
3. Start the server:

   python app.py

4. Open http://127.0.0.1:5000

## API endpoints

- `GET /` serve the AVL UI
- `GET /health` health check
- `GET /api/avl/state` current tree and traversals
- `POST /api/avl/insert` body `{ "value": <int> }`
- `POST /api/avl/delete` body `{ "value": <int> }`
- `POST /api/avl/search` body `{ "value": <int> }`
- `POST /api/avl/reset` clear tree
- `POST /api/avl/random` body `{ "count": <int> }` with count in 3..20
