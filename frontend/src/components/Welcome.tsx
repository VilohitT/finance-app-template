"use client";

import Link from "next/link";

type Props = {
  hasApiKey: boolean;
};

export default function Welcome({ hasApiKey }: Props) {
  return (
    <div className="flex-1 overflow-y-auto flex items-center justify-center px-6 py-12">
      <div className="max-w-2xl">
        <h2 className="text-2xl font-semibold text-gray-100 mb-3">
          Welcome to your finance app
        </h2>
        <p className="text-sm text-gray-400 mb-8 leading-relaxed">
          Indian-context personal investment planning. The agent reads your
          foundation files (<code>goals.md</code>, <code>portfolio.md</code>,{" "}
          <code>user-principles.md</code>) and runs Indian-tax-aware analyses
          locally on your machine. Your data never leaves your device.
        </p>

        <ol className="space-y-4">
          <Step
            number={1}
            title="Set your Anthropic API key"
            done={hasApiKey}
            action={
              !hasApiKey && (
                <Link
                  href="/settings"
                  className="inline-block mt-2 px-3 py-1.5 bg-blue-600 hover:bg-blue-500 rounded text-sm text-white"
                >
                  Open settings →
                </Link>
              )
            }
          >
            The agent uses Claude (Anthropic) to reason. You bring your own key.
            Get one at{" "}
            <a
              href="https://console.anthropic.com/"
              target="_blank"
              rel="noreferrer noopener"
              className="text-blue-300 underline"
            >
              console.anthropic.com
            </a>
            .
          </Step>

          <Step
            number={2}
            title="Bootstrap the data layer"
            done={false}
            action={
              hasApiKey && (
                <div className="mt-2 text-xs text-gray-500">
                  In the chat below, type <code className="text-blue-300">/setup</code>{" "}
                  and press Enter.
                </div>
              )
            }
          >
            Verifies Python prereqs, loads today&apos;s NAVs for ~14,000 Indian
            mutual funds, and confirms your foundation files are present.
          </Step>

          <Step number={3} title="Capture your situation" done={false}>
            Run these interviews in order:
            <ul className="mt-2 space-y-1 text-xs text-gray-400">
              <li>
                <code className="text-blue-300">/finance-grill</code> — goals, income, risk tolerance (~30 min)
              </li>
              <li>
                <code className="text-blue-300">/principles-grill</code> — sleeve targets, routing, glide paths (~10-15 min)
              </li>
              <li>
                <code className="text-blue-300">/portfolio-grill</code> — every holding (~20-40 min)
              </li>
            </ul>
          </Step>

          <Step number={4} title="Use it" done={false}>
            <code className="text-blue-300">/portfolio-review</code> weekly,{" "}
            <code className="text-blue-300">/fund-allocate</code> when fresh
            money arrives, <code className="text-blue-300">/laws-refresh</code> after the
            Union Budget.
          </Step>
        </ol>

        <p className="text-xs text-gray-600 mt-10">
          Tip: type <code className="text-blue-300">/</code> to open the skill picker.
        </p>
      </div>
    </div>
  );
}

function Step({
  number,
  title,
  done,
  action,
  children,
}: {
  number: number;
  title: string;
  done: boolean;
  action?: React.ReactNode;
  children: React.ReactNode;
}) {
  return (
    <li className="flex gap-4">
      <div
        className={`flex-shrink-0 w-7 h-7 rounded-full flex items-center justify-center text-xs font-medium border ${
          done
            ? "bg-green-600/30 border-green-500/50 text-green-200"
            : "bg-gray-800 border-gray-700 text-gray-400"
        }`}
      >
        {done ? "✓" : number}
      </div>
      <div className="flex-1 pb-1">
        <div className="text-sm font-medium text-gray-200">{title}</div>
        <div className="text-sm text-gray-400 mt-1 leading-relaxed">{children}</div>
        {action}
      </div>
    </li>
  );
}
