# Paint editor

## by Elina Adibi, Samuel Scott, William Hurley and Luke Winter

### Class: CST 205

### Date: 07-26-24

### How to run the program:

- Pull the project
- Go to your terminal and create an environment
- Install all the necessary libraries (See import statements)
- Navigate to the projects root folder and run the command "flask --app app --debug run"
- Copy the URL and open it in your web browser
- Enjoy!

### Github:

https://github.com/lukewintercsumb/cst205-project

### Trello board:

https://trello.com/b/DeZ9LBxt/team-477

### Future work:

In our future work, we could improve the efficiency and speed of the algorithm that makes the selection. This could be accomplished by switiching more of the calculations to vectorized operations supplied by numpy. We could also downsample the image, make the selection and then upsample the selection again. Combined, this could make the selection process take only a couple of second which would be reasonable.
Additionally, we could improve the selection algorithm. One idea is to restrict selected pixels to be only those that are directly connected to one of the initially selected pixels. For example if I click on a pixel (x, y), another pixel (x2, y2) would only be selected if it has the required color distance, and it touches another "selected" pixel. That means the selection would grow outwards from a selected pixel and we would avoid pixel islands.
Additionaly, we could make the color replacement algorithm more performant, by using even more sophisticated approaches. Currently we have no idea how such an algorithm would look, but we assume there are many options presented on the internet.
Lastly, we can certainly improve the UI design, and user experience, by allowing any image to be uploaded, and not just the preselected options. Potentially, we could add more sophisticated image editing tools like contrast and saturation.
