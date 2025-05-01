from fastapi import FastAPI, Query
from fastapi.responses import RedirectResponse

app = FastAPI()

# Replace this with your actual Google Form's pre-filled URL format
GOOGLE_FORM_BASE_URL = "https://docs.google.com/forms/d/e/YOUR_FORM_ID/viewform"

@app.get("/apply-loan")
def apply_loan(name: str = Query(...), email: str = Query(...), amount: int = Query(...)):
    # Replace entry.X with actual field entry IDs from your Google Form
    google_form_url = (
        f"{GOOGLE_FORM_BASE_URL}?"
        f"entry.123456789={name}&entry.987654321={email}&entry.456789123={amount}"
    )
    return RedirectResponse(url=google_form_url)

if __name__ == "_main_":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)