# LMArenaBridge API

An unofficial bridge that exposes LMArena models through OpenAI-compatible and Anthropic-compatible HTTP endpoints. It includes a password-protected dashboard, API-key authentication, model discovery, streaming, reasoning output, search citations, image generation, and vision input where supported by the selected model.

> [!WARNING]
> This project is reverse-engineered and is not affiliated with or endorsed by LMArena. Upstream endpoints, models, authentication, and bot protection can change without notice. Use it responsibly and comply with LMArena's terms and applicable model-provider terms.

## Endpoints

| Purpose | Method and path |
| --- | --- |
| Dashboard | `GET /dashboard` |
| Health check | `GET /api/v1/health` |
| Model list | `GET /api/v1/models` |
| OpenAI chat completions | `POST /api/v1/chat/completions` |
| Anthropic messages | `POST /api/v1/messages` |
| Interactive API documentation | `GET /docs` |

The API base URL is `https://YOUR-SERVICE.onrender.com/api/v1`. All API endpoints other than health and the dashboard require this header when an API key is configured:

```http
Authorization: Bearer YOUR_API_KEY
```

## Deploy on Render's free web-service tier

The included [`Dockerfile`](Dockerfile) installs the Linux libraries and Camoufox browser required by the bridge, runs as a non-root user, listens on Render's dynamic `PORT`, and binds to `0.0.0.0`. The included [`render.yaml`](render.yaml) provides a one-click Blueprint configuration.

### Before deploying

1. Fork this repository to your GitHub account (or push it to a repository Render can access).
2. Prepare two strong secrets:
   - **Admin password**: protects `/dashboard`.
   - **API key**: protects API requests. A value such as `sk-lmab-` followed by a long random string is suitable.
3. Optionally obtain your LMArena `arena-auth-prod-v1` cookie. Sign in to LMArena in your own browser, open the browser developer tools, go to **Application/Storage → Cookies**, select the LMArena/Arena site, and copy the cookie's **value**. Treat this value like a password. Do not put it in Git, screenshots, logs, or issues.

An auth token is optional because the bridge can attempt anonymous browser signup, but a valid token generally makes operation more reliable. Tokens expire and may need replacement.

### Option A: deploy with the Render Blueprint (recommended)

1. Sign in at [Render](https://render.com/) and connect GitHub.
2. Select **New → Blueprint**.
3. Select your fork/repository. Render detects `render.yaml`.
4. Confirm that the service type is **Web Service**, runtime is **Docker**, and plan is **Free**.
5. Render will generate `ADMIN_PASSWORD` and `API_KEY`. Enter `AUTH_TOKEN` and, optionally, `CF_CLEARANCE` (a fallback Cloudflare cookie) when prompted, or leave them empty to try anonymous operation.
6. Apply the Blueprint and wait for the Docker build and deployment to finish.
7. In the service's **Environment** page, reveal/copy the generated `ADMIN_PASSWORD` and `API_KEY`; store them in a password manager.
8. Open `https://YOUR-SERVICE.onrender.com/api/v1/health`. A `healthy` or `degraded` JSON response confirms that the web server is reachable. `degraded` during startup can mean models or Cloudflare cookies have not been refreshed yet.
9. Open `https://YOUR-SERVICE.onrender.com/dashboard`, sign in with `ADMIN_PASSWORD`, and verify token/model status.

### Option B: configure the web service manually

Create **New → Web Service**, connect the repository, and use:

| Setting | Value |
| --- | --- |
| Language/runtime | `Docker` |
| Branch | The branch you want Render to deploy |
| Dockerfile path | `./Dockerfile` |
| Instance type | `Free` |
| Health check path | `/api/v1/health` |
| Auto-deploy | Your preference |

Do not set a custom start command. The Docker image already starts `python -m src.main`. Do not hard-code a port: Render supplies `PORT` automatically.

Add these environment variables under **Environment**:

| Variable | Required | Description |
| --- | --- | --- |
| `ADMIN_PASSWORD` | Yes | Strong password for `/dashboard`. Never retain the default `admin` on a public deployment. |
| `API_KEY` | Yes | Secret used in the Bearer authorization header. It overrides keys in `config.json`. |
| `API_RPM` | No | Per-key requests per minute, from 1 to 1000. Default is `120`; the Blueprint uses `60`. |
| `AUTH_TOKEN` | Recommended | Value of an `arena-auth-prod-v1` cookie. It overrides auth tokens in `config.json`. `ARENA_AUTH_TOKEN` is accepted as an alias. |
| `CF_CLEARANCE` | No | Fallback value for the Cloudflare `cf_clearance` cookie. Used only when the browser-based Cloudflare challenge could not fetch one and none is stored in `config.json`; a freshly fetched cookie takes priority. Never written back to `config.json`. |
| `PYTHONUNBUFFERED` | No | Set to `1` for immediate Python logs; already present in the Blueprint/image. |

Mark secret values as secret in Render. After changing a variable, deploy/restart the service so the new value is loaded.

### Free-tier limitations

- The service may spin down after inactivity. The first request after sleep can take longer while Render starts the container and the browser initializes.
- Free instances have limited memory and CPU. Browser automation is resource-intensive, so concurrent requests, strict models, or image workflows can fail under memory pressure. Reduce traffic/RPM or move to a larger instance if this occurs.
- The free web service filesystem is ephemeral. Dashboard edits, generated API keys, refreshed cookies, usage statistics, and other changes written to `config.json` can disappear after a restart or redeploy. Keep `ADMIN_PASSWORD`, `API_KEY`, `AUTH_TOKEN`, and (when needed) `CF_CLEARANCE` in Render environment variables; those are reapplied on every boot.
- Do not add a Render persistent disk merely to expose secrets. If you choose a paid persistent disk, mount and configuration paths need additional application changes; this repository uses its working directory by default.
- Render's outbound IP addresses are shared/dynamic on free services. LMArena or Cloudflare may challenge or rate-limit them. A successful deployment does not guarantee that every upstream model will work.

## Use the API

Replace `BASE_URL`, `API_KEY`, and model names in the examples. Always retrieve the live model list first because available public names change.

### List models

```bash
curl -sS "$BASE_URL/api/v1/models" \
  -H "Authorization: Bearer $API_KEY"
```

### OpenAI-compatible chat (non-streaming)

```bash
curl -sS "$BASE_URL/api/v1/chat/completions" \
  -H "Authorization: Bearer $API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "MODEL_NAME_FROM_MODELS_ENDPOINT",
    "messages": [
      {"role": "system", "content": "Answer concisely."},
      {"role": "user", "content": "What is a binary search?"}
    ],
    "stream": false
  }'
```

The answer is in `choices[0].message.content`. Reasoning-capable models may also return `reasoning_content`; search models may return `citations`; image models return an image URL as Markdown content.

### Streaming chat

```bash
curl -N "$BASE_URL/api/v1/chat/completions" \
  -H "Authorization: Bearer $API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "MODEL_NAME_FROM_MODELS_ENDPOINT",
    "messages": [{"role": "user", "content": "Write a short haiku."}],
    "stream": true
  }'
```

Streaming uses server-sent events (SSE). Read each `data:` JSON event until `data: [DONE]`. Lines beginning with `:` are keep-alive comments and can be ignored.

### Python with the OpenAI SDK

```bash
pip install openai
```

```python
import os
from openai import OpenAI

client = OpenAI(
    api_key=os.environ["API_KEY"],
    base_url=os.environ["BASE_URL"] + "/api/v1",
)

response = client.chat.completions.create(
    model="MODEL_NAME_FROM_MODELS_ENDPOINT",
    messages=[{"role": "user", "content": "Hello!"}],
)
print(response.choices[0].message.content)
```

For streaming, pass `stream=True` and iterate over the returned stream.

### Anthropic-compatible messages

```bash
curl -sS "$BASE_URL/api/v1/messages" \
  -H "Authorization: Bearer $API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "MODEL_NAME_FROM_MODELS_ENDPOINT",
    "max_tokens": 1024,
    "system": "Be helpful.",
    "messages": [{"role": "user", "content": "Hello!"}],
    "stream": false
  }'
```

The Anthropic compatibility layer supports the core text message shape; it is not a guarantee that every Anthropic SDK feature or tool-use feature is implemented.

### Vision input

For a model whose input capabilities include images, send an OpenAI-style content array. Base64 data URLs are supported; arbitrary external image URLs are currently skipped.

```json
{
  "model": "VISION_MODEL_NAME",
  "messages": [{
    "role": "user",
    "content": [
      {"type": "text", "text": "Describe this image."},
      {"type": "image_url", "image_url": {"url": "data:image/png;base64,BASE64_DATA"}}
    ]
  }],
  "stream": false
}
```

## Dashboard and authentication notes

- Visit `/dashboard` and sign in with `ADMIN_PASSWORD`.
- Environment values take priority over the checked-in configuration. When `API_KEY` is set, it is the only API key loaded at startup; use that value even if the dashboard previously displayed another key.
- `AUTH_TOKEN` similarly takes priority over dashboard auth-token entries after each restart.
- The API rejects a missing or invalid Bearer token whenever an API key is configured.
- The health endpoint intentionally does not require an API key so Render can monitor the service.

## Local Docker run

```bash
docker build -t lmarena-bridge .
docker run --rm -p 8000:8000 \
  -e PORT=8000 \
  -e ADMIN_PASSWORD='replace-me' \
  -e API_KEY='sk-lmab-replace-me' \
  -e AUTH_TOKEN='optional-arena-cookie-value' \
  -e CF_CLEARANCE='optional-fallback-cf-clearance-cookie' \
  lmarena-bridge
```

Then use `http://localhost:8000/api/v1` as the API base URL.

## Troubleshooting

- **401 from this service:** include `Authorization: Bearer ...` and ensure it exactly matches Render's `API_KEY`.
- **Upstream 401:** replace the expired `AUTH_TOKEN` in Render and redeploy.
- **403/reCAPTCHA or Cloudflare errors:** retry later, open the dashboard and refresh tokens/models, or use a valid Arena token. Shared hosting IPs can remain blocked.
- **429:** respect `Retry-After`, lower request frequency, or wait for the upstream limit to reset.
- **No models / degraded health:** allow startup discovery to finish, inspect Render logs, and use the dashboard's refresh action.
- **Container killed or browser launch fails:** this commonly indicates free-tier memory pressure. Reduce concurrency or upgrade the Render instance.
- **Slow first response:** the service may be waking from sleep and then launching Camoufox. Streaming calls emit keep-alives while upstream work runs.

Never post your Render environment values, Arena cookie, API key, or full logs containing those values in a public issue.

## License

See [LICENSE](LICENSE).
