'use client';

import { useEditor, EditorContent } from '@tiptap/react';
import StarterKit from '@tiptap/starter-kit';
import Placeholder from '@tiptap/extension-placeholder';
import { useEffect, useCallback } from 'react';

export interface TiptapEditorProps {
  content: any; // Tiptap JSON format
  onChange: (content: any) => void;
  sectionId: string;
  threadId: string;
  userId: number;
  editable?: boolean;
  placeholder?: string;
  className?: string;
}

export default function TiptapEditor({
  content,
  onChange,
  sectionId,
  threadId,
  userId,
  editable = true,
  placeholder = 'Start editing...',
  className = '',
}: TiptapEditorProps) {
  const editor = useEditor({
    extensions: [
      StarterKit.configure({
        // Disable some features if needed
        // heading: false,
        // blockquote: false,
      }),
      Placeholder.configure({
        placeholder,
      }),
    ],
    content: content || {
      type: 'doc',
      content: [
        {
          type: 'paragraph',
        },
      ],
    },
    editable,
    immediatelyRender: false, // Fix SSR hydration mismatch
    onUpdate: ({ editor }) => {
      const json = editor.getJSON();
      onChange(json);
    },
    editorProps: {
      attributes: {
        class: `prose prose-sm sm:prose lg:prose-lg xl:prose-2xl mx-auto focus:outline-none min-h-[200px] ${className}`,
      },
    },
  });

  // Update editor content when prop changes (for realtime sync)
  useEffect(() => {
    if (editor && content) {
      const currentContent = JSON.stringify(editor.getJSON());
      const newContent = JSON.stringify(content);
      
      // Only update if content actually changed (avoid infinite loops)
      if (currentContent !== newContent) {
        // Use setContent with emitUpdate: false to prevent triggering onUpdate
        editor.commands.setContent(content, { emitUpdate: false });
      }
    }
  }, [editor, content]);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      if (editor) {
        editor.destroy();
      }
    };
  }, [editor]);

  if (!editor) {
    return (
      <div className="border rounded-lg p-4 min-h-[200px] bg-gray-50 animate-pulse">
        <p className="text-gray-400">Loading editor...</p>
      </div>
    );
  }

  return (
    <div className="border rounded-lg p-4 bg-white focus-within:ring-2 focus-within:ring-blue-500 focus-within:border-blue-500 transition-all">
      <EditorContent editor={editor} />
    </div>
  );
}

