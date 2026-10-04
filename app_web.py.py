"""
app_web.py - Streamlit Web Version of Secrets within Pixels
"""

import streamlit as st
from PIL import Image
import io
import steganography as stego
import crypto_utils as crypto

st.set_page_config(
    page_title="Secrets within Pixels",
    page_icon="🔒",
    layout="centered"
)

st.title("🔒 Secrets within Pixels – The Art of Steganography")
st.markdown("A web-based LSB steganography and AES-Fernet cryptographic tool.")

tab1, tab2 = st.tabs(["🛡️ Hide Secret (Encode)", "🔍 Extract Secret (Decode)"])

# --- TAB 1: ENCODE ---
with tab1:
    st.header("Embed a Secret Message")
    
    uploaded_file = st.file_uploader("Choose a cover image (PNG recommended):", type=["png", "jpg", "jpeg", "bmp"])
    
    if uploaded_file is not None:
        cover_image = Image.open(uploaded_file)
        st.image(cover_image, caption="Uploaded Cover Image", use_column_width=True)
        
        # Calculate capacity
        cap = stego.get_image_capacity(cover_image)
        st.info(f"📊 Image Capacity: **{cap['usable_bytes']:,} bytes** available.")
        
        secret_message = st.text_area("Type your secret message here:")
        
        use_encryption = st.checkbox("Encrypt secret with password (AES-Fernet)")
        password = ""
        if use_encryption:
            password = st.text_input("Enter Encryption Password:", type="password")
            
        if st.button("⚡ Encode & Generate Stego Image"):
            if not secret_message:
                st.error("Please enter a secret message.")
            elif use_encryption and not password:
                st.error("Please enter a password for encryption.")
            else:
                try:
                    payload = secret_message
                    if use_encryption:
                        payload = crypto.encrypt_message(secret_message, password)
                        
                    stego_img = stego.encode_lsb(cover_image, payload)
                    
                    # Save to bytes buffer for download
                    buf = io.BytesIO()
                    stego_img.save(buf, format="PNG")
                    byte_im = buf.getvalue()
                    
                    st.success("Secret successfully hidden in pixels!")
                    st.download_button(
                        label="📥 Download Stego-Image (PNG)",
                        data=byte_im,
                        file_name="stego_secret.png",
                        mime="image/png"
                    )
                except Exception as e:
                    st.error(f"Error during encoding: {e}")

# --- TAB 2: DECODE ---
with tab2:
    st.header("Extract a Secret Message")
    
    stego_file = st.file_uploader("Choose a stego-image (.png):", type=["png"], key="decode_uploader")
    
    if stego_file is not None:
        stego_image = Image.open(stego_file)
        st.image(stego_image, caption="Uploaded Stego-Image", use_column_width=True)
        
        decode_password = st.text_input("Enter Password (if message was encrypted):", type="password", key="decode_pass")
        
        if st.button("🔓 Extract Secret Message"):
            try:
                raw_payload = stego.decode_lsb(stego_image)
                
                if crypto.is_encrypted(raw_payload):
                    if not decode_password:
                        st.warning("This message is encrypted! Please enter the password above.")
                    else:
                        decrypted = crypto.decrypt_message(raw_payload, decode_password)
                        st.success("Message decrypted successfully!")
                        st.text_area("Revealed Secret:", value=decrypted, height=150)
                else:
                    st.success("Plaintext message extracted successfully!")
                    st.text_area("Revealed Secret:", value=raw_payload, height=150)
                    
            except Exception as e:
                st.error(f"Extraction failed: {e}")