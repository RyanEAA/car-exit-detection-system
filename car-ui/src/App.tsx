import { useState } from "react";
import type { ChangeEvent } from "react";
const VITE_API_URL = import.meta.env.VITE_API_URL;
type DetectionResult = {
  is_car: boolean;
  view?: string;
  license_plate?: string | null;
};

function App() {
  const [image, setImage] = useState<File | null>(null);
  const [preview, setPreview] = useState<string | null>(null);
  const [result, setResult] = useState<DetectionResult | null>(null);
  const [loading, setLoading] = useState<boolean>(false);

  const handleImageChange = (e: ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0] || null;
    setImage(file);

    if (file) {
      setPreview(URL.createObjectURL(file));
    }
  };

  const handleUpload = async () => {
    if (!image) return;

    setLoading(true);
    setResult(null);

    const formData = new FormData();
    formData.append("file", image);

    try {
      const res = await fetch(`${import.meta.env.VITE_API_URL}/detect/`, {
        method: "POST",
        body: formData,
      });

      const data: DetectionResult = await res.json();
      setResult(data);
    } catch (err) {
      console.error(err);
      alert("Error connecting to API");
    }

    setLoading(false);
  };

  return (
    <div style={{ padding: 40, fontFamily: "Arial" }}>
      <h1>🚗 Car Detection App</h1>

      <input type="file" accept="image/*" onChange={handleImageChange} />

      {preview && (
        <div style={{ marginTop: 20 }}>
          <img
            src={preview}
            alt="preview"
            style={{ width: 300, borderRadius: 10 }}
          />
        </div>
      )}

      <button
        onClick={handleUpload}
        disabled={loading}
        style={{
          marginTop: 20,
          padding: "10px 20px",
          fontSize: 16,
          cursor: "pointer",
        }}
      >
        {loading ? "Processing..." : "Run Detection"}
      </button>

      {result && (
        <div style={{ marginTop: 30 }}>
          <h2>Results:</h2>
          <p><strong>Car detected:</strong> {result.is_car ? "Yes" : "No"}</p>
          <p><strong>View:</strong> {result.view ?? "N/A"}</p>

          {result.license_plate && (
            <p><strong>Plate:</strong> {result.license_plate}</p>
          )}
        </div>
      )}
    </div>
  );
}

export default App;