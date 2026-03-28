import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import api from '../api';
import './Recommendations.css';

export default function Recommendations() {
  const [recommendations, setRecommendations] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [expandedId, setExpandedId] = useState(null);

  const toggleExpand = (id) => {
    setExpandedId(prev => (prev === id ? null : id));
  };

  useEffect(() => {
    // Scroll to top on load
    window.scrollTo(0, 0);

    const fetchRecommendations = async () => {
      try {
        setLoading(true);
        // Add a slight delay to show the "AI generating" effect, as ML inference can be near instant but we want the UX
        await new Promise(resolve => setTimeout(resolve, 800));
        
        const response = await api.get('/ngos/recommendations');
        setRecommendations(response.data);
      } catch (err) {
        console.error("Failed to fetch recommendations", err);
        setError("Our AI engine is currently resting. Please try again later.");
      } finally {
        setLoading(false);
      }
    };

    fetchRecommendations();
  }, []);

  return (
    <div className="recommendations-page">
      <div className="recommendations-header reveal visible">
        <h1 className="recommendations-title">
          Intelligent <span className="highlight">Matching</span>
        </h1>
        <p className="recommendations-subtitle">
          Our XGBoost recommendation engine constantly analyzes impact scores, funding ratios, and application backlogs to bring you the highest-impact NGOs actively seeking resources.
        </p>
      </div>

      {loading ? (
        <div className="generating-container reveal visible reveal-delay-2">
          <div className="spinner"></div>
          <div className="generating-text">AI Generating Intelligence...</div>
        </div>
      ) : error ? (
        <div className="error-message">
          <p>{error}</p>
        </div>
      ) : (
        <div className="recommendations-grid reveal visible reveal-delay-2">
          {recommendations.length > 0 ? (
            recommendations.map((rec, index) => (
              <div 
                key={rec.ngo.id} 
                className={`recommendation-card reveal visible`} 
                style={{ animationDelay: `${index * 0.15 + 0.3}s` }}
              >
                <div className={`rank-badge ${rec.rank === 1 ? 'rank-1' : ''}`}>
                  #{rec.rank}
                </div>
                
                <div className="ngo-info">
                  <h3 className="ngo-name">{rec.ngo.name}</h3>
                  <p className="ngo-description">
                    {rec.ngo.description || "Leading impact across various development sectors. Actively matching student scholarships."}
                  </p>
                </div>

                <div className="impact-score-container">
                  <span className="impact-score-label">Predicted Impact Score</span>
                  <div className="impact-score-value">
                    {rec.impact_score > 0 ? rec.impact_score : "High"} 
                    <span>/ 100</span>
                  </div>
                </div>

                <div className="action-bar">
                  <button 
                    className="action-btn"
                    onClick={() => toggleExpand(rec.ngo.id)}
                  >
                    {expandedId === rec.ngo.id ? "Hide Details" : "View Profile"}
                  </button>
                </div>

                {expandedId === rec.ngo.id && rec.features && (
                  <div className="ngo-details-expanded reveal visible">
                    <h4 className="insights-heading">AI Engine Insights</h4>
                    <ul className="insights-list">
                      <li>
                        <span className="insight-label">Funding Ratio:</span> 
                        <span className="insight-value">{(rec.features.funding_ratio * 100).toFixed(1)}%</span>
                      </li>
                      <li>
                        <span className="insight-label">Disbursement Speed:</span> 
                        <span className="insight-value">{rec.features.disbursement_velocity_days.toFixed(0)} days</span>
                      </li>
                      <li>
                        <span className="insight-label">Area Target Income:</span> 
                        <span className="insight-value">₹{rec.features.avg_student_income.toLocaleString(undefined, { maximumFractionDigits: 0 })}/yr</span>
                      </li>
                      <li>
                        <span className="insight-label">Application Backlog:</span> 
                        <span className="insight-value">{rec.features.application_backlog} scholars</span>
                      </li>
                    </ul>
                  </div>
                )}
              </div>
            ))
          ) : (
            <div className="no-results">
              <p>No recommendations available at the moment. Please check back later.</p>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
