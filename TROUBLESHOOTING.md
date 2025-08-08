# Troubleshooting Connection Issues

## Common Issues and Solutions

### 1. "Connection lost" Error

**Symptoms:**
- UI shows "Connection lost" status
- Backend keeps hitting the same endpoint repeatedly
- No data appears in the UI

**Solutions:**

#### Check if server is running:
```bash
curl http://localhost:8000/health
```

#### Check if frontend is running:
```bash
curl http://localhost:5173
```

#### Start both services properly:
```bash
./start.sh
```

### 2. CORS Issues

**Symptoms:**
- Browser console shows CORS errors
- Connection fails immediately

**Solutions:**
- The server already has CORS middleware configured
- Make sure you're accessing the frontend from `http://localhost:5173`
- Check that the server URL in `.env` is correct

### 3. API Key Issues

**Symptoms:**
- Analysis fails with API key errors
- No search results returned

**Solutions:**
- Check that `OPENAI_API_KEY` is set in `server/.env`
- Check that `PERPLEXITY_API_KEY` is set in `server/.env`
- Restart the server after changing environment variables

### 4. Network Issues

**Symptoms:**
- Timeout errors
- Slow response times

**Solutions:**
- Check your internet connection
- Try a different ticker symbol
- Check if the APIs (OpenAI, Perplexity) are accessible

### 5. Port Conflicts

**Symptoms:**
- "Address already in use" errors
- Services won't start

**Solutions:**
```bash
# Kill processes on ports 8000 and 5173
lsof -ti:8000 | xargs kill -9
lsof -ti:5173 | xargs kill -9
```

### 6. Dependencies Issues

**Symptoms:**
- Import errors
- Module not found errors

**Solutions:**
```bash
# Install server dependencies
cd server
pip install -r requirements.txt

# Install frontend dependencies
cd ../web
npm install
```

## Debug Steps

1. **Check server logs:**
   - Look for error messages in the terminal where the server is running
   - Check for API key errors or network timeouts

2. **Check browser console:**
   - Open Developer Tools (F12)
   - Look for JavaScript errors or network failures

3. **Test API directly:**
   ```bash
   curl "http://localhost:8000/api/stream?ticker=AAPL"
   ```

4. **Check environment variables:**
   ```bash
   cat server/.env
   cat web/.env
   ```

## Quick Fix

If all else fails, try this complete reset:

```bash
# Stop all services
pkill -f "uvicorn\|vite"

# Clear any cached data
rm -rf server/__pycache__
rm -rf web/node_modules/.vite

# Restart everything
./start.sh
``` 