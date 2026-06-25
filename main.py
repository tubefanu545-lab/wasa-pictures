async function uploadPhoto() {
    const password = document.getElementById('passwordInput').value;
    const title = document.getElementById('titleInput').value.trim();
    const category = document.getElementById('categoryInput').value;
    const fileInput = document.getElementById('fileInput');
    const uploadBtn = document.getElementById('uploadBtn');
    
    if(!password || !title || fileInput.files.length === 0) { alert("All fields are required!"); return; }
    if(password !== "wasa") { alert("Wrong admin password!"); return; }
    
    const file = fileInput.files[0];
    uploadBtn.innerText = "Uploading... ⏳";
    uploadBtn.disabled = true;

    // ፎቶውን ወደ ጽሑፍ (Base64) የመቀየሪያ ዘዴ
    const reader = new FileReader();
    reader.readAsDataURL(file);
    reader.onload = async function () {
        const base64Image = reader.result;

        try {
            // በቀጥታ ወደ Render ሰርቨርህ መላክ
            const res = await fetch(`${API_BASE_URL}/photos`, {
                method: "POST", 
                headers: { 
                    "Content-Type": "application/json",
                    "X-Photo-Title": title, 
                    "X-Photo-Category": category, 
                    "X-Admin-Password": password 
                }, 
                body: JSON.stringify({ url: base64Image }) // የፎቶው ጽሑፍ ይሄዳል
            });

            if(res.ok) { 
                document.getElementById('titleInput').value = ""; 
                fileInput.value = ""; 
                toggleMenu(); 
                loadPhotos(); 
            } else { 
                alert("Failed to save to database."); 
            }
        } catch (err) { 
            alert("Error: " + err.message); 
        } finally {
            uploadBtn.innerText = "Upload Photo";
            uploadBtn.disabled = false;
        }
    };
}