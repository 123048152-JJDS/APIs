Usando la powerShell


…or create a new repository on the command line
echo "# PruevaCodigosPython" >> README.md
git init
git add README.md
## Nota: Si deseas agregar todos los archivos en el repositorio, usa "git add ."
git commit -m "first commit"
git branch -M main
git remote add origin https://github.com/USER/Repositorio.git
git push -u origin main


…or push an existing repository from the command line
git remote add origin https://github.com/USER/Repositorio.git
git branch -M main
git push -u origin main


…or create a new repository on the command line
echo "# PruevaCodigosPython" >> README.md
git init
git add README.md
git commit -m "first commit"
git branch -M main
git remote add origin git@github.com:USER/Repositorio.git
git push -u origin main

…or push an existing repository from the command line
git remote add origin git@github.com:USER/Repositorio.git
git branch -M main
git push -u origin main


Comandos clave
Comando	Función
git status	    Verifica cambios no guardados.
git log	        Muestra el historial de commits.
git pull	    Actualiza el repositorio local.
git branch	    Gestiona ramas.


Para actualizar el repositorio local con los últimos cambios del remoto:
git pull origin main

git status
git add .
git commit -m "Mensaje del commit"
git pull origin main   # (recomendado antes de push para actualizar)
git push origin main