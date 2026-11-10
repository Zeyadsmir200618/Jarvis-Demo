// 1. Changed BotMessageSquare to Bot (a more universally supported icon)
import { Bot, Code, Terminal, Info, Zap } from 'lucide-react';

interface AgentIconProps {
  agentName?: string;
  className?: string;
}

const mergeClasses = (...classes: Array<string | undefined | null | false>) =>
  classes.filter(Boolean).join(' ');

// 2. Added 'export default' so it works no matter how the parent file imports it
export default function AgentIcon({ agentName, className }: AgentIconProps) {
  const icons: Record<string, JSX.Element> = {
    'General Companion Agent': <Bot className={mergeClasses('w-3 h-3 text-cyan-400', className)} />,
    'Web & Code Builder Agent': <Code className={mergeClasses('w-3 h-3 text-emerald-400', className)} />,
    'Root Cause Analysis Agent': <Terminal className={mergeClasses('w-3 h-3 text-rose-400', className)} />,
    'System': <Info className={mergeClasses('w-3 h-3 text-blue-400', className)} />,
  };

  return icons[agentName as string] || <Zap className={mergeClasses('w-3 h-3 text-neutral-400', className)} />;
}

// Keep the named export as well just in case other files use it!
export { AgentIcon as AgentIconNamed };