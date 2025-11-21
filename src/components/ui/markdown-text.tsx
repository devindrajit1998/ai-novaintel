import React from 'react';

interface MarkdownTextProps {
  content: string;
  className?: string;
}

/**
 * Simple markdown text renderer that handles basic markdown syntax
 * Converts **text** to bold, *text* to italic, and preserves line breaks
 */
export function MarkdownText({ content, className = '' }: MarkdownTextProps) {
  if (!content) return null;

  // Split by double line breaks to preserve paragraphs
  const paragraphs = content.split(/\n\n+/);
  
  return (
    <div className={`prose prose-sm max-w-none ${className}`}>
      {paragraphs.map((paragraph, pIndex) => {
        if (!paragraph.trim()) return null;
        
        // Process inline markdown within paragraph
        const processedParagraph = processMarkdown(paragraph.trim());
        
        return (
          <p key={pIndex} className="mb-4 last:mb-0 leading-relaxed">
            {processedParagraph}
          </p>
        );
      })}
    </div>
  );
}

/**
 * Process markdown syntax and return React elements
 * Handles **bold**, *italic*, and line breaks
 */
function processMarkdown(text: string): React.ReactNode[] {
  const parts: React.ReactNode[] = [];
  let currentIndex = 0;
  const textLength = text.length;
  
  while (currentIndex < textLength) {
    const remainingText = text.substring(currentIndex);
    
    // Look for **bold** first (has priority over *italic*)
    const boldMatch = remainingText.match(/^\*\*(.+?)\*\*/);
    if (boldMatch) {
      // Add bold text
      parts.push(
        <strong key={`bold-${parts.length}`} className="font-semibold text-foreground">
          {boldMatch[1]}
        </strong>
      );
      currentIndex += boldMatch[0].length;
      continue;
    }
    
    // Look for *italic* (but not **bold**)
    const italicMatch = remainingText.match(/^\*(?!\*)(.+?)\*/);
    if (italicMatch) {
      // Add italic text
      parts.push(
        <em key={`italic-${parts.length}`} className="italic">
          {italicMatch[1]}
        </em>
      );
      currentIndex += italicMatch[0].length;
      continue;
    }
    
    // Look for line break
    if (text[currentIndex] === '\n') {
      parts.push(<br key={`break-${parts.length}`} />);
      currentIndex++;
      continue;
    }
    
    // Find the next markdown syntax or end of string
    let nextMarkdown = textLength;
    const nextBold = text.indexOf('**', currentIndex);
    const nextItalic = text.indexOf('*', currentIndex);
    const nextBreak = text.indexOf('\n', currentIndex);
    
    if (nextBold !== -1 && nextBold < nextMarkdown) nextMarkdown = nextBold;
    if (nextItalic !== -1 && nextItalic < nextMarkdown) nextMarkdown = nextItalic;
    if (nextBreak !== -1 && nextBreak < nextMarkdown) nextMarkdown = nextBreak;
    
    // Add plain text
    const plainText = text.substring(currentIndex, nextMarkdown);
    if (plainText) {
      parts.push(plainText);
    }
    currentIndex = nextMarkdown;
  }
  
  return parts.length > 0 ? parts : [text];
}


