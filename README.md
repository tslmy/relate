# Relate

How is statistical mechanics related to a lollipop? A [breadth-first search][bfs] on [WikiData](https://www.wikidata.org/) tells you how. 

![logo](static/logo.svg)

[TOC]

*Disclaimer: Icon made by [Freepik](http://www.freepik.com) from [Flaticon](http://www.flaticon.com/).*

## Usage

Go to [here](http://relator.herokuapp.com/), input names of the two concepts for which you want to check their relation, and hit "relate".

![](https://ww3.sinaimg.cn/large/006tKfTcgy1fj4i69romtj305303nweg.jpg)

##Example

How is Phitsanulok, a province in Thailand, related to lollipops (the sweets)?

Relator says:

> Phitsanulok is located in the administrative territorial entity called "Thailand", which has diplomatic relation with France. 
>
> Lollipop has sucrose as its part, which has the chemical element "hydrogen". Hydrogen is discovered in France.

![](https://ww2.sinaimg.cn/large/006tKfTcgy1fj4i5m8cn3j308e0o70u3.jpg)

## Behind the Scenes

At its core, Relate is a Python-driven [web app](https://en.wikipedia.org/wiki/Web_application) that uses the [Wikidata API](https://www.wikidata.org/w/api.php) to fetch entity properties as [edges](https://en.wikipedia.org/wiki/Glossary_of_graph_theory_terms#edge) on a [graph](https://en.wikipedia.org/wiki/Glossary_of_graph_theory_terms#graph). 

A script explores this graph in a [breadth-first search][bfs] manner with two scrapers from both vertices specified by the user. Once scrapers meet at a vertice, a [path](https://en.wikipedia.org/wiki/Glossary_of_graph_theory_terms#path) is found.

[bfs]: https://en.wikipedia.org/wiki/Breadth-first_search

Here is a sketch of how it works:

![](https://ww4.sinaimg.cn/large/006tKfTcgy1fj4ioqf0fej31kw1bge81.jpg)

