'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { Sparkles, Briefcase, TestTube2, Wallet } from 'lucide-react';

const navigation = [
  { name: 'AI Ideas', href: '/', icon: Sparkles },
  { name: 'Trading', href: '/paper-trading', icon: Wallet },
  { name: 'Portfolio', href: '/portfolio', icon: Briefcase },
  { name: 'Backtest', href: '/backtest', icon: TestTube2 },
];

export default function Navigation() {
  const pathname = usePathname();

  return (
    <nav className="bg-gray-900 border-b border-gray-800">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16">
          <div className="flex items-center">
            <div className="flex-shrink-0">
              <h1 className="text-xl font-bold text-white">
                AI Trading Simulator
              </h1>
            </div>
            <div className="hidden md:block ml-10">
              <div className="flex space-x-4">
                {navigation.map((item) => {
                  const Icon = item.icon;
                  const isActive = pathname === item.href;
                  return (
                    <Link
                      key={item.name}
                      href={item.href}
                      className={`px-3 py-2 rounded-md text-sm font-medium flex items-center gap-2 transition-colors ${
                        isActive
                          ? 'bg-gray-800 text-white'
                          : 'text-gray-300 hover:bg-gray-700 hover:text-white'
                      }`}
                    >
                      <Icon className="w-4 h-4" />
                      {item.name}
                    </Link>
                  );
                })}
              </div>
            </div>
          </div>
        </div>
      </div>
    </nav>
  );
}
