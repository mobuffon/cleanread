import { BookOpen, Smartphone, Zap, Shield } from 'lucide-react'

const features = [
  {
    icon: BookOpen,
    title: 'Smart Layout Detection',
    description: 'Intelligently detects and handles multi-column layouts, headers, and footers',
  },
  {
    icon: Smartphone,
    title: 'E-Reader Optimized',
    description: 'Perfect formatting for Kindle and other e-ink devices with reflowable text',
  },
  {
    icon: Zap,
    title: 'Fast Processing',
    description: 'GPU-accelerated conversion for quick results, even with large documents',
  },
  {
    icon: Shield,
    title: 'Privacy First',
    description: 'Your documents are processed securely and deleted after conversion',
  },
]

export default function Features() {
  return (
    <div id="features" className="mt-20">
      <div className="text-center mb-12">
        <h2 className="text-3xl font-bold text-gray-900 mb-4">
          Why Choose CleanRead?
        </h2>
        <p className="text-lg text-gray-600">
          Convert your PDFs with intelligent processing and optimization
        </p>
      </div>

      <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-8">
        {features.map((feature) => (
          <div
            key={feature.title}
            className="bg-white rounded-xl p-6 shadow-md hover:shadow-lg transition-shadow"
          >
            <div className="bg-primary-100 w-12 h-12 rounded-lg flex items-center justify-center mb-4">
              <feature.icon className="w-6 h-6 text-primary-600" />
            </div>
            <h3 className="text-xl font-semibold mb-2 text-gray-900">
              {feature.title}
            </h3>
            <p className="text-gray-600">
              {feature.description}
            </p>
          </div>
        ))}
      </div>

      <div id="how-it-works" className="mt-20 bg-white rounded-2xl shadow-lg p-8">
        <h2 className="text-3xl font-bold text-center text-gray-900 mb-8">
          How It Works
        </h2>
        <div className="grid md:grid-cols-3 gap-8">
          <div className="text-center">
            <div className="bg-primary-500 text-white w-12 h-12 rounded-full flex items-center justify-center mx-auto mb-4 text-xl font-bold">
              1
            </div>
            <h3 className="text-xl font-semibold mb-2">Upload PDF</h3>
            <p className="text-gray-600">
              Drag and drop or select your PDF file
            </p>
          </div>
          <div className="text-center">
            <div className="bg-primary-500 text-white w-12 h-12 rounded-full flex items-center justify-center mx-auto mb-4 text-xl font-bold">
              2
            </div>
            <h3 className="text-xl font-semibold mb-2">AI Processing</h3>
            <p className="text-gray-600">
              Our AI extracts and optimizes the content
            </p>
          </div>
          <div className="text-center">
            <div className="bg-primary-500 text-white w-12 h-12 rounded-full flex items-center justify-center mx-auto mb-4 text-xl font-bold">
              3
            </div>
            <h3 className="text-xl font-semibold mb-2">Download EPUB</h3>
            <p className="text-gray-600">
              Get your optimized EPUB file ready for reading
            </p>
          </div>
        </div>
      </div>
    </div>
  )
}
