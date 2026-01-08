# Appendix: Obtaining a Google AI Studio API Key 🔑
To run the simulation engine in this study, you need an API key from Google. As of early 2026, the **Gemini 1.5 Flash** model is available via a free tier that is perfect for this type of research.

## 🛠️ Step-by-Step Instructions
1.  **Visit Google AI Studio**
    Go to [aistudio.google.com](https://aistudio.google.com/)

2.  **Sign In**
    Log in with your standard Google/Gmail account.

3.  **Generate the Key**
    * On the left-hand sidebar, click on **"Get API key"**.
    * Click the button labeled **"Create API key in new project"** or **Create API key**
    * Name your key: `persona-password-project`
    * Cloud project: **Create project**
    * Name your project: `persona-password-project-key`
    * Click **Create project**
    * Click **Create key**

4.  **Copy and Secure**:
    * Click on the new key
    * Copy the API key (it usually starts with `AIza...`).
    * **Important:** Never share this key or upload it to GitHub. This repository's `.gitignore` is already configured to hide `config.py`.

## ⚙️ Local Configuration
Once you have your key, you need to make it accessible to the scripts in this repo.

1.  Navigate to the root directory of the project.
2.  Create a file named `config.py`.
3.  Add the following line to that file:

```python
API_KEY = "PASTE_YOUR_KEY_HERE"
```
