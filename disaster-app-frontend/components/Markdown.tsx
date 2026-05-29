import React from 'react';

interface MarkdownProps {
  content: string;
}

export default function Markdown({ content }: MarkdownProps) {
  if (!content) return null;

  const lines = content.split('\n');
  const renderedElements: React.ReactNode[] = [];
  
  let inList = false;
  let listItems: React.ReactNode[] = [];
  let listType: 'ul' | 'ol' = 'ul';

  const parseInlineStyles = (text: string) => {
    // Step 1: Split bold text (**bold**)
    const parts = text.split(/(\*\*.*?\*\*)/g);
    return parts.flatMap((part, index) => {
      if (part.startsWith('**') && part.endsWith('**')) {
        return [<strong key={`b-${index}`} className="font-bold text-slate-900 dark:text-white">{part.slice(2, -2)}</strong>];
      }
      
      // Step 2: Split inline code (`code`)
      const codeParts = part.split(/(`.*?`)/g);
      return codeParts.map((subPart, subIndex) => {
        if (subPart.startsWith('`') && subPart.endsWith('`')) {
          return (
            <code key={`code-${index}-${subIndex}`} className="bg-slate-100 dark:bg-slate-800/80 text-slate-800 dark:text-slate-200 px-1 py-0.5 rounded font-mono text-xs border border-slate-200/40 dark:border-slate-700/40">
              {subPart.slice(1, -1)}
            </code>
          );
        }
        return subPart;
      });
    });
  };

  const flushList = (key: number) => {
    if (listItems.length > 0) {
      const ListTag = listType;
      renderedElements.push(
        <ListTag key={`list-${key}`} className={listType === 'ul' ? 'list-disc pl-5 my-2.5 space-y-1.5 text-slate-700 dark:text-slate-300' : 'list-decimal pl-5 my-2.5 space-y-1.5 text-slate-700 dark:text-slate-300'}>
          {listItems}
        </ListTag>
      );
      listItems = [];
      inList = false;
    }
  };

  let codeBlockContent: string[] = [];
  let inCodeBlock = false;

  for (let i = 0; i < lines.length; i++) {
    const line = lines[i];

    // Code block handling
    if (line.trim().startsWith('```')) {
      if (inCodeBlock) {
        // End of code block
        renderedElements.push(
          <pre key={`code-${i}`} className="bg-slate-900 dark:bg-slate-950 text-slate-100 p-3.5 rounded-lg font-mono text-[11px] overflow-x-auto my-2.5 border border-slate-850 whitespace-pre shadow-sm leading-relaxed max-w-full">
            <code className="block">{codeBlockContent.join('\n')}</code>
          </pre>
        );
        codeBlockContent = [];
        inCodeBlock = false;
      } else {
        // Start of code block
        flushList(i);
        inCodeBlock = true;
      }
      continue;
    }

    if (inCodeBlock) {
      codeBlockContent.push(line);
      continue;
    }

    // Headers
    if (line.startsWith('# ')) {
      flushList(i);
      renderedElements.push(<h1 key={`h1-${i}`} className="text-lg font-bold mt-4 mb-2 text-slate-900 dark:text-white border-b border-slate-100 dark:border-slate-800 pb-1">{parseInlineStyles(line.slice(2))}</h1>);
      continue;
    }
    if (line.startsWith('## ')) {
      flushList(i);
      renderedElements.push(<h2 key={`h2-${i}`} className="text-base font-bold mt-3 mb-1.5 text-slate-900 dark:text-white">{parseInlineStyles(line.slice(3))}</h2>);
      continue;
    }
    if (line.startsWith('### ')) {
      flushList(i);
      renderedElements.push(<h3 key={`h3-${i}`} className="text-sm font-bold mt-2 mb-1 text-slate-900 dark:text-white">{parseInlineStyles(line.slice(4))}</h3>);
      continue;
    }

    // Unordered List Items
    if (line.trim().startsWith('* ') || line.trim().startsWith('- ')) {
      if (!inList || listType !== 'ul') {
        flushList(i);
        inList = true;
        listType = 'ul';
      }
      listItems.push(<li key={`li-${i}`} className="text-sm leading-relaxed">{parseInlineStyles(line.trim().slice(2))}</li>);
      continue;
    }

    // Ordered List Items
    const olMatch = line.trim().match(/^(\d+)\.\s(.*)/);
    if (olMatch) {
      if (!inList || listType !== 'ol') {
        flushList(i);
        inList = true;
        listType = 'ol';
      }
      listItems.push(<li key={`li-${i}`} className="text-sm leading-relaxed">{parseInlineStyles(olMatch[2])}</li>);
      continue;
    }

    // Empty line
    if (line.trim() === '') {
      flushList(i);
      renderedElements.push(<div key={`empty-${i}`} className="h-1.5" />);
      continue;
    }

    // Normal paragraph
    flushList(i);
    renderedElements.push(<p key={`p-${i}`} className="text-sm leading-relaxed my-1.5 text-slate-800 dark:text-slate-200">{parseInlineStyles(line)}</p>);
  }

  // Flush any remaining list items at the end
  flushList(lines.length);

  return <div className="space-y-1.5 w-full break-words">{renderedElements}</div>;
}
