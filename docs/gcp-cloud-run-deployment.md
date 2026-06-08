# GCP Cloud Run Deployment

This app is deployed as two Cloud Run services:

- `demo-adk-backend`: FastAPI backend, Google ADK orchestration, Vertex AI calls.
- `demo-adk-frontend`: Streamlit frontend, calls the backend `/api/chat` endpoint.

## 0. Install Google Cloud CLI

The deployment commands use `gcloud`. If your shell prints `bash: gcloud: command not found`, install and initialize the Google Cloud CLI first.

On macOS Apple Silicon:

```bash
curl -O https://dl.google.com/dl/cloudsdk/channels/rapid/downloads/google-cloud-cli-darwin-arm.tar.gz
tar -xf google-cloud-cli-darwin-arm.tar.gz
./google-cloud-sdk/install.sh
./google-cloud-sdk/bin/gcloud init
```

Restart your terminal, then confirm the CLI is available:

```bash
gcloud --version
```

## 1. Set Variables

```bash
export PROJECT_ID="your-gcp-project-id"
export REGION="us-central1"
export REPOSITORY="demo-adk"

gcloud config set project "$PROJECT_ID"
```

## 2. Enable APIs

```bash
gcloud services enable run.googleapis.com
gcloud services enable artifactregistry.googleapis.com
gcloud services enable cloudbuild.googleapis.com
gcloud services enable aiplatform.googleapis.com
```

## 3. Create Artifact Registry

```bash
gcloud artifacts repositories create "$REPOSITORY" \
  --repository-format=docker \
  --location="$REGION" \
  --description="Demo multi-agent ADK images"
```

## 4. Create Runtime Service Account

```bash
gcloud iam service-accounts create demo-adk-runtime \
  --display-name="Demo ADK Runtime"

gcloud projects add-iam-policy-binding "$PROJECT_ID" \
  --member="serviceAccount:demo-adk-runtime@$PROJECT_ID.iam.gserviceaccount.com" \
  --role="roles/aiplatform.user"
```

## 5. Build Images

Rebuild an image any time its Dockerfile or copied source files change.

```bash
gcloud builds submit \
  --config cloudbuild.backend.yaml \
  --substitutions "_IMAGE=$REGION-docker.pkg.dev/$PROJECT_ID/$REPOSITORY/backend"

gcloud builds submit \
  --config cloudbuild.frontend.yaml \
  --substitutions "_IMAGE=$REGION-docker.pkg.dev/$PROJECT_ID/$REPOSITORY/frontend"
```

## 6. Deploy Backend

```bash
gcloud run deploy demo-adk-backend \
  --image "$REGION-docker.pkg.dev/$PROJECT_ID/$REPOSITORY/backend:latest" \
  --region "$REGION" \
  --service-account "demo-adk-runtime@$PROJECT_ID.iam.gserviceaccount.com" \
  --set-env-vars "APP_ENV=prod,VERTEX_AI_AUTH_METHOD=vertex_ai,VERTEX_AI_PROJECT=$PROJECT_ID,VERTEX_AI_REGION=$REGION\
  --update-env-vars "LANGFUSE_PUBLIC_KEY=pk-lf-a...,LANGFUSE_SECRET_KEY=sk-lf-...,LANGFUSE_BASE_URL=https://cloud.langfuse.com,LANGFUSE_BACKEND_TRACE_NAME=demo_multi_agent_adk.backend,LANGFUSE_TAGS=google-adk,prod,cloud-run" \
  --ingress all \
  --default-url \
  --allow-unauthenticated
```

Check the backend:

```bash
export BACKEND_URL="$(gcloud run services describe demo-adk-backend --region "$REGION" --format='value(status.url)')"
curl "$BACKEND_URL/api/health"
```

Expected response:

```json
{"status":"ok"}
```

If you get a Google `404` page, confirm that `BACKEND_URL` points to the backend Cloud Run service in the same region:

```bash
echo "$BACKEND_URL"
gcloud run services describe demo-adk-backend --region "$REGION" --format='value(status.url)'
gcloud run services list --region "$REGION"
```

Then confirm the service allows direct internet traffic:

```bash
gcloud run services describe demo-adk-backend \
  --region "$REGION" \
  --format='yaml(metadata.annotations)'
```

Look for:

```yaml
run.googleapis.com/ingress: all
```

If the value is missing or not `all`, redeploy the backend with `--ingress all`, then retry with the URL returned by `services describe`.

Also confirm the default `run.app` URL is enabled:

```bash
gcloud run services describe demo-adk-backend \
  --region "$REGION" \
  --format='yaml(metadata.annotations)'
```

If you see `run.googleapis.com/default-url-disabled: 'true'`, re-enable the default URL:

```bash
gcloud run services update demo-adk-backend \
  --region "$REGION" \
  --default-url
```

## 7. Deploy Frontend

```bash
gcloud run deploy demo-adk-frontend \
  --image "$REGION-docker.pkg.dev/$PROJECT_ID/$REPOSITORY/frontend:latest" \
  --region "$REGION" \
  --set-env-vars "APP_ENV=prod,APP_BACKEND_URL=$BACKEND_URL,VERTEX_AI_AUTH_METHOD=vertex_ai,VERTEX_AI_PROJECT=$PROJECT_ID,VERTEX_AI_REGION=$REGION" \
  --ingress all \
  --default-url \
  --allow-unauthenticated
```

Check the frontend:

```bash
export FRONTEND_URL="$(gcloud run services describe demo-adk-frontend --region "$REGION" --format='value(status.url)')"
curl -I "$FRONTEND_URL"
```

Expected response headers include `content-type: text/html`.

If you get `content-type: application/json` with a `404`, the frontend Cloud Run service is likely running the backend image. Confirm the deployed image:

```bash
gcloud run services describe demo-adk-frontend \
  --region "$REGION" \
  --format='value(spec.template.spec.containers[0].image)'
```

It should end with `/frontend:latest`. If it ends with `/backend:latest`, redeploy the frontend with the command above.

## 8. Optional Langfuse Configuration

Prefer Secret Manager for production secrets. For a quick deployment, pass keys as Cloud Run env vars:

```bash
gcloud run services update demo-adk-backend \
  --region "$REGION" \
  --set-env-vars "LANGFUSE_PUBLIC_KEY=pk-lf-...,LANGFUSE_SECRET_KEY=sk-lf-...,LANGFUSE_BASE_URL=https://cloud.langfuse.com,LANGFUSE_TAGS=google-adk,prod,cloud-run"
```

Apply the same values to `demo-adk-frontend` if frontend tracing is enabled.

The backend flushes Langfuse traces after each ADK run so Cloud Run does not leave queued observations unsent when an instance goes idle.

## 9. Troubleshoot Backend 500s

If the frontend shows `Backend request failed with status 500`, the frontend reached the backend but the ADK/Vertex AI call failed. Read the backend logs for the real provider error:

```bash
gcloud run services logs read demo-adk-backend \
  --region "$REGION" \
  --limit 100
```

You can also call the backend directly:

```bash
curl -i "$BACKEND_URL/api/chat" \
  -H "Content-Type: application/json" \
  -d '{"prompt":"hi"}'
```

Common causes are missing Vertex AI permissions for the runtime service account, disabled Vertex AI API, unsupported model or region, and project quota errors.

## 10. Optional CORS

The current Streamlit frontend calls the backend from server-side Python, so CORS is usually not required. If you add browser-side API calls later, configure allowed origins:

```bash
gcloud run services update demo-adk-backend \
  --region "$REGION" \
  --set-env-vars "BACKEND_CORS_ALLOWED_ORIGINS=https://your-frontend-domain.example.com"
```

## Runtime Configuration

The containers copy `config.example.yaml` and select the `prod` environment with `APP_ENV=prod`. Deployment-specific values are overridden by environment variables:

- `APP_BACKEND_URL`
- `APP_TITLE`
- `APP_PROMPT_LABEL`
- `ADK_MODEL_NAME`
- `VERTEX_AI_AUTH_METHOD`
- `VERTEX_AI_PROJECT`
- `VERTEX_AI_REGION`
- `GOOGLE_API_KEY` or `GEMINI_API_KEY`
- `LANGFUSE_PUBLIC_KEY`
- `LANGFUSE_SECRET_KEY`
- `LANGFUSE_BASE_URL`
- `LANGFUSE_BACKEND_TRACE_NAME`
- `LANGFUSE_FRONTEND_TRACE_NAME`
- `LANGFUSE_TAGS`
- `BACKEND_CORS_ALLOWED_ORIGINS`
