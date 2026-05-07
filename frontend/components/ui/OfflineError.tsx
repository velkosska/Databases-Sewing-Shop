import React from "react";

interface Props {
  message?: string;
}

export default function OfflineError({ message }: Props) {
  return (
    <div className="min-h-screen bg-neutral-50 flex items-center justify-center px-4">
      <div className="max-w-md w-full bg-white border border-neutral-200 rounded-2xl p-10 text-center shadow-sm">
        <div className="w-14 h-14 rounded-full bg-red-50 flex items-center justify-center mx-auto mb-6">
          <svg
            className="w-7 h-7 text-red-500"
            fill="none"
            stroke="currentColor"
            strokeWidth={1.5}
            viewBox="0 0 24 24"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              d="M12 9v3.75m-9.303 3.376c-.866 1.5.217 3.374 1.948 3.374h14.71c1.73 0 2.813-1.874 1.948-3.374L13.949 3.378c-.866-1.5-3.032-1.5-3.898 0L2.697 16.126ZM12 15.75h.007v.008H12v-.008Z"
            />
          </svg>
        </div>

        <h1 className="text-xl font-semibold text-neutral-900 mb-2">
          Cannot reach the backend
        </h1>

        <p className="text-sm text-neutral-500 mb-6 leading-relaxed">
          {message ?? "The Django development server is not running or is unreachable."}
        </p>

        <div className="bg-neutral-50 border border-neutral-200 rounded-xl p-4 text-left mb-6">
          <p className="text-xs font-medium text-neutral-500 uppercase tracking-wide mb-2">
            Start both servers
          </p>
          <code className="block text-xs text-neutral-800 font-mono leading-6">
            # Terminal 1 — Django<br />
            cd sewing_shop_project<br />
            source venv/bin/activate<br />
            python manage.py runserver<br />
            <br />
            # Terminal 2 — Next.js<br />
            cd sewing_shop_project/frontend<br />
            npm run dev
          </code>
        </div>

        <p className="text-xs text-neutral-400">
          Or use <code className="font-mono">./start.sh</code> to start both at once.
        </p>
      </div>
    </div>
  );
}
