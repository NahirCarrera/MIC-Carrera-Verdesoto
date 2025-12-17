<!DOCTYPE html>
<html lang="{{ str_replace('_', '-', app()->getLocale()) }}">
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>AuditAI - Iniciar Sesión</title>
    @vite(['resources/css/app.css', 'resources/js/app.js'])
</head>
<body class="antialiased">

    <div class="min-h-screen flex items-center justify-center relative overflow-hidden bg-gray-900">
        
        <div class="absolute inset-0 z-0">
            <img src="https://cdn.prod.website-files.com/630dfafcb284c6e437ab4f4a/67956cc73d3f3dc62deb9e47_6313ab1eb85cef55a1f462c6_hero-image-minified.png" 
                 alt="Background" 
                 class="w-full h-full object-cover opacity-60">
            <div class="absolute inset-0 bg-gray-900/40 backdrop-blur-sm"></div>
        </div>

        <div class="relative z-10 w-full max-w-md p-6">
            
            <div class="bg-white/90 backdrop-blur-xl rounded-2xl shadow-2xl overflow-hidden border border-white/20 transform transition-all hover:scale-[1.01] duration-500">
                
                <div class="px-8 pt-8 pb-4 text-center">
                    <div class="inline-flex items-center justify-center w-12 h-12 rounded-full bg-indigo-100 text-indigo-600 mb-4 shadow-sm">
                        <svg xmlns="http://www.w3.org/2000/svg" class="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                        </svg>
                    </div>
                    <h1 class="text-2xl font-bold text-gray-800 tracking-tight">AuditAI</h1>
                    <p class="text-sm text-gray-500 mt-2">Control de Calidad Alimentaria con Inteligencia Artificial</p>
                </div>

                <div class="px-8 pb-8 pt-2">
                    
                    @if ($errors->any())
                        <div class="mb-4 bg-red-50 text-red-600 p-3 rounded-lg text-sm flex items-start border border-red-100">
                            <svg class="w-5 h-5 mr-2 mt-0.5 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"></path></svg>
                            <div>
                                <span class="font-bold block">Acceso denegado</span>
                                {{ $errors->first() }}
                            </div>
                        </div>
                    @endif

                    <form method="POST" action="{{ route('login') }}" class="space-y-5">
                        @csrf

                        <div class="space-y-1">
                            <label for="email" class="text-sm font-semibold text-gray-600 ml-1">Correo Electrónico</label>
                            <input id="email" name="email" type="email" required autofocus
                                   class="w-full px-4 py-3 rounded-xl bg-gray-50 border border-gray-200 text-gray-800 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:bg-white transition-all duration-200"
                                   placeholder="usuario@empresa.com"
                                   value="{{ old('email') }}">
                        </div>

                        <div class="space-y-1">
                            <div class="flex justify-between items-center ml-1">
                                <label for="password" class="text-sm font-semibold text-gray-600">Contraseña</label>
                                @if (Route::has('password.request'))
                                    <a href="{{ route('password.request') }}" class="text-xs font-medium text-indigo-600 hover:text-indigo-500 transition-colors">
                                        ¿Olvidaste tu contraseña?
                                    </a>
                                @endif
                            </div>
                            <input id="password" name="password" type="password" required
                                   class="w-full px-4 py-3 rounded-xl bg-gray-50 border border-gray-200 text-gray-800 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:bg-white transition-all duration-200"
                                   placeholder="••••••••">
                        </div>

                        <div class="flex items-center ml-1">
                            <input id="remember_me" name="remember" type="checkbox" 
                                   class="h-4 w-4 text-indigo-600 focus:ring-indigo-500 border-gray-300 rounded cursor-pointer">
                            <label for="remember_me" class="ml-2 block text-sm text-gray-600 cursor-pointer select-none">
                                Mantener sesión iniciada
                            </label>
                        </div>

                        <button type="submit" 
                                class="w-full py-3.5 px-4 bg-indigo-600 hover:bg-indigo-700 text-white font-bold rounded-xl shadow-lg shadow-indigo-500/30 transform hover:-translate-y-0.5 transition-all duration-200 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500">
                            Ingresar al Sistema
                        </button>
                    </form>

                    <div class="mt-6 text-center border-t border-gray-100 pt-6">
                        <p class="text-sm text-gray-500">
                            ¿Aún no tienes acceso? 
                            <a href="{{ route('register') }}" class="font-bold text-indigo-600 hover:text-indigo-800 transition-colors">
                                Crear cuenta
                            </a>
                        </p>
                    </div>

                </div>
            </div>
            
            <p class="text-center text-gray-400 text-xs mt-6 font-medium tracking-wide">
                &copy; {{ date('Y') }} AuditAI. Powered by Computer Vision.
            </p>

        </div>
    </div>

</body>
</html>