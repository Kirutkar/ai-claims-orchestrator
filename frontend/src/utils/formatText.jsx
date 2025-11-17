import React from "react";

/**
 * Formats text with markdown-like formatting:
 * - **bold** text
 * - Numbered lists (1., 2., etc.)
 * - Bullet points
 * - Line breaks
 */
export const FormattedText = ({ text, className = "", style = {} }) => {
  if (!text) return null;

  // Split by single newlines first to handle numbered lists and bullets
  const lines = text.split("\n").filter((line) => line.trim());

  const formattedElements = [];
  let currentParagraph = [];

  for (let i = 0; i < lines.length; i++) {
    const line = lines[i].trim();

    // Check if it's a numbered list item (starts with number.)
    const numberedMatch = line.match(/^(\d+\.\s+)(.+)$/);
    if (numberedMatch) {
      // If we have accumulated paragraph text, render it first
      if (currentParagraph.length > 0) {
        formattedElements.push(
          <div key={`para-${i}`} style={{ marginBottom: "1rem" }}>
            {formatInlineText(currentParagraph.join(" "))}
          </div>
        );
        currentParagraph = [];
      }

      // Render numbered list item
      formattedElements.push(
        <div
          key={`num-${i}`}
          style={{
            marginBottom: "0.75rem",
            paddingLeft: "1rem",
            lineHeight: "1.6",
          }}
        >
          <span
            style={{
              fontWeight: "700",
              marginRight: "0.5rem",
              color: "var(--text-color)",
            }}
          >
            {numberedMatch[1]}
          </span>
          <span style={{ color: "var(--text-secondary)" }}>
            {formatInlineText(numberedMatch[2])}
          </span>
        </div>
      );
      continue;
    }

    // Check if it's a bullet point
    const bulletMatch = line.match(/^[-•]\s+(.+)$/);
    if (bulletMatch) {
      // If we have accumulated paragraph text, render it first
      if (currentParagraph.length > 0) {
        formattedElements.push(
          <div key={`para-${i}`} style={{ marginBottom: "1rem" }}>
            {formatInlineText(currentParagraph.join(" "))}
          </div>
        );
        currentParagraph = [];
      }

      // Render bullet point
      formattedElements.push(
        <div
          key={`bullet-${i}`}
          style={{
            marginBottom: "0.5rem",
            paddingLeft: "1rem",
            display: "flex",
            lineHeight: "1.6",
          }}
        >
          <span
            style={{
              marginRight: "0.75rem",
              color: "var(--text-color)",
              fontWeight: "600",
            }}
          >
            •
          </span>
          <span style={{ color: "var(--text-secondary)", flex: 1 }}>
            {formatInlineText(bulletMatch[1])}
          </span>
        </div>
      );
      continue;
    }

    // Regular text line - accumulate into paragraph
    if (line) {
      currentParagraph.push(line);
    }

    // If next line is empty or a list item, render accumulated paragraph
    if (
      i === lines.length - 1 ||
      (i < lines.length - 1 &&
        (lines[i + 1].match(/^\d+\.\s+/) ||
          lines[i + 1].match(/^[-•]\s+/) ||
          lines[i + 1].trim() === ""))
    ) {
      if (currentParagraph.length > 0) {
        formattedElements.push(
          <div
            key={`para-${i}`}
            style={{ marginBottom: "1rem", lineHeight: "1.6" }}
          >
            {formatInlineText(currentParagraph.join(" "))}
          </div>
        );
        currentParagraph = [];
      }
    }
  }

  return (
    <div className={className} style={style}>
      {formattedElements.length > 0
        ? formattedElements
        : formatInlineText(text)}
    </div>
  );
};

/**
 * Formats inline text with bold markers
 */
const formatInlineText = (text) => {
  const parts = [];
  const boldRegex = /\*\*([^*]+)\*\*/g;
  let lastIndex = 0;
  let match;

  while ((match = boldRegex.exec(text)) !== null) {
    // Add text before the match
    if (match.index > lastIndex) {
      parts.push(
        <span key={`text-${lastIndex}`}>
          {text.substring(lastIndex, match.index)}
        </span>
      );
    }

    // Add bold text
    parts.push(
      <strong key={`bold-${match.index}`} style={{ fontWeight: "700" }}>
        {match[1]}
      </strong>
    );
    lastIndex = boldRegex.lastIndex;
  }

  // Add remaining text
  if (lastIndex < text.length) {
    parts.push(
      <span key={`text-${lastIndex}`}>{text.substring(lastIndex)}</span>
    );
  }

  return parts.length > 0 ? parts : text;
};

/**
 * Formats recommendations list
 */
export const FormattedRecommendations = ({
  recommendations,
  className = "",
}) => {
  if (!recommendations || recommendations.length === 0) return null;

  return (
    <div className={className} style={{ marginTop: "1rem" }}>
      <strong
        style={{
          fontSize: "1rem",
          fontWeight: "700",
          display: "block",
          marginBottom: "0.75rem",
        }}
      >
        Recommendations:
      </strong>
      <ul
        style={{
          marginTop: "0.5rem",
          paddingLeft: "1.5rem",
          listStyleType: "disc",
        }}
      >
        {recommendations.map((rec, idx) => (
          <li
            key={idx}
            style={{
              marginBottom: "0.5rem",
              lineHeight: "1.6",
              color: "var(--text-secondary)",
            }}
          >
            {formatInlineText(rec)}
          </li>
        ))}
      </ul>
    </div>
  );
};
