# Railway Deployment Guide for Sevafy

This guide explains how to deploy the Sevafy project (Frontend + Backend combined) to [Railway](https://railway.app/).

## Prerequisites
- A Railway account.
- This project pushed to a GitHub repository.

## Step 1: Create a New Project on Railway
1. Log in to your [Railway Dashboard](https://railway.app/dashboard).
2. Click **+ New Project**.
3. Select **Deploy from GitHub repo**.
4. Choose your `Sevafy` repository.
5. In the "Project Settings" (or when prompted), Railway should automatically detect the `Dockerfile` at the root.

## Step 2: Configure Environment Variables
Go to the **Variables** tab of your service in Railway and add the following variables. Use the values from your local `.env` file:

| Key | Value |
| :--- | :--- |
| `DATABASE_URL` | *Your Neon PostgreSQL connection string* |
| `SECRET_KEY` | *Your generated random secret* |
| `GOOGLE_CLIENT_ID` | *Your Google OAuth Client ID* |
| `BLOCKCHAIN_RPC_URL` | `https://1rpc.io/sepolia` |
| `BLOCKCHAIN_WS_URL` | `wss://1rpc.io/sepolia` |
| `CONTRACT_ADDRESS` | `0x0C2ebaF34f165EF173D0bFFc2795447977894942` |
| `WALLET_PRIVATE_KEY` | *Your wallet private key* |
| `GENAI_API_KEY` | *Your GenAI API key* |

> [!IMPORTANT]
> Railway handles the `PORT` automatically. Our `Dockerfile` now exposes `8080` (Railway's default). Make sure you confirm `8080` in the **Networking** settings to generate your domain.

## Step 3: Deployment
1. Once variables are added, Railway will trigger a new deployment.
2. In the **Settings** tab, scroll down to **Networking**.
3. Click **Generate Domain** or add a custom domain to get your public URL.
4. Your website should now be live at that URL!

## Step 4: Verification
1. Visit the domain provided by Railway.
2. Ensure the login page loads (checks frontend).
3. Attempt to login or view data (checks backend & database connection).
4. Check the "Transparent Ledger" to verify blockchain connectivity.

## Troubleshooting
- **Build Errors**: Check the **Deployments** tab logs in Railway. Ensure all dependencies are in `package.json` and `requirements.txt`.
- **Database Connection**: Ensure the `DATABASE_URL` includes `?sslmode=require`.
- **API Errors**: If API calls fail, check the **Deployments > View Logs** to see backend errors.
