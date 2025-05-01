import React, { useState } from 'react';
import './CardViewer.css';

const CardViewer = () => {
  const [imageUrl, setImageUrl] = useState(null);
  const [loading, setLoading] = useState(false);
  const [cardType, setCardType] = useState("");

  const fetchCardImage = async (type) => {
    // If same button is clicked again, hide the image
    if (type === cardType && imageUrl) {
      setImageUrl(null);
      setCardType("");
      return;
    }

    setLoading(true);
    setCardType(type);
    try {
      const response = await fetch(`http://localhost:8000/get-card-image?type=${type}`);
      const data = await response.json();
      setImageUrl(data.image_url);
    } catch (error) {
      console.error("Error fetching card:", error);
      setImageUrl(null);
    }
    setLoading(false);
  };

  return (
    <div className="card-viewer-container">
      <h2>Document Viewer</h2>
      <div className="button-group">
        <button
          className={cardType === "pan" && imageUrl ? "active" : ""}
          onClick={() => fetchCardImage("pan")}
        >
          PAN
        </button>
        <button
          className={cardType === "aadhar" && imageUrl ? "active" : ""}
          onClick={() => fetchCardImage("aadhar")}
        >
          Aadhar
        </button>
      </div>

      {loading && <p>Loading {cardType} card...</p>}

      {!loading && imageUrl && (
        <img
          className="document-image"
          src={imageUrl}
          alt={`${cardType} card`}
        />
      )}
    </div>
  );
};

export default CardViewer;
