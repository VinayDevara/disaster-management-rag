import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import Link from 'next/link'
import { CheckCircle, Mail } from 'lucide-react'

export default function Page() {
  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-950 via-slate-900 to-slate-950 flex items-center justify-center p-6">
      <div className="w-full max-w-md">
        <Card className="bg-slate-800/50 border-slate-700/50 shadow-2xl">
          <CardHeader>
            <div className="flex justify-center mb-4">
              <div className="w-16 h-16 bg-gradient-to-br from-green-500 to-emerald-500 rounded-full flex items-center justify-center">
                <CheckCircle className="w-8 h-8 text-white" />
              </div>
            </div>
            <CardTitle className="text-2xl text-center text-white">
              Registration Successful!
            </CardTitle>
            <CardDescription className="text-center">
              Please verify your email to activate your account
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-6">
            <div className="p-4 bg-blue-500/10 border border-blue-500/30 rounded-lg">
              <div className="flex gap-3">
                <Mail className="w-5 h-5 text-blue-400 flex-shrink-0 mt-0.5" />
                <div>
                  <p className="text-sm font-medium text-blue-300 mb-1">Check Your Email</p>
                  <p className="text-xs text-blue-200">
                    We&apos;ve sent a confirmation email to your inbox. Click the link to verify your account and get started.
                  </p>
                </div>
              </div>
            </div>

            <div className="space-y-3">
              <p className="text-sm text-gray-300">Once confirmed, you can:</p>
              <ul className="text-xs text-gray-400 space-y-2">
                <li className="flex gap-2">
                  <span className="text-blue-400">✓</span>
                  <span>Access the disaster management dashboard</span>
                </li>
                <li className="flex gap-2">
                  <span className="text-blue-400">✓</span>
                  <span>Monitor real-time disaster updates</span>
                </li>
                <li className="flex gap-2">
                  <span className="text-blue-400">✓</span>
                  <span>Chat with the AI assistant</span>
                </li>
                <li className="flex gap-2">
                  <span className="text-blue-400">✓</span>
                  <span>Save chat history and analytics</span>
                </li>
              </ul>
            </div>

            <Link href="/auth/login" className="block w-full">
              <Button className="w-full bg-blue-600 hover:bg-blue-700 text-white">
                Go to Sign In
              </Button>
            </Link>

            <p className="text-xs text-center text-gray-500">
              Didn&apos;t receive the email? Check your spam folder or try signing up again.
            </p>
          </CardContent>
        </Card>
      </div>
    </div>
  )
}
