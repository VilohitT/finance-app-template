"use client";

import ReactMarkdown, { Components } from "react-markdown";
import remarkGfm from "remark-gfm";

const components: Components = {
  // Render code blocks with our prose-msg styling (from globals.css).
  code({ className, children, ...props }) {
    return (
      <code className={className} {...props}>
        {children}
      </code>
    );
  },
  // External links open in new tab.
  a({ href, children }) {
    return (
      <a
        href={href}
        target="_blank"
        rel="noreferrer noopener"
        className="text-blue-300 hover:text-blue-200 underline"
      >
        {children}
      </a>
    );
  },
};

export default function Markdown({ text }: { text: string }) {
  return (
    <div className="prose-msg text-sm text-gray-100 break-words">
      <ReactMarkdown remarkPlugins={[remarkGfm]} components={components}>
        {text}
      </ReactMarkdown>
    </div>
  );
}
