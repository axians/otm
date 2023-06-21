<!DOCTYPE html>
<html lang="en">

<head>
    <title>{{title}}</title>
    <link rel="icon" type="image/png" href="favicon.png"/>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/github-fork-ribbon-css/0.2.3/gh-fork-ribbon.min.css" />
    <style>
         body {
            font-family: sans-serif;
            background-color: white;
            margin: 0;
            padding: 0;
         }
         .left {
            width: 450px;
            height: 100%;
            box-shadow: inset 0 0 0 2000px rgba(0, 0, 0, .6);
            float: left;
         }
         .top_container {
             display: flex;
             justify-content: center;
             margin-top: 8%;
         }
         .top_container h3 {
             max-width: 380px;
             text-align: center;
             color: rgba(0, 0, 0, 0.9);
         }
         .container {
            background-color: rgba(255, 255, 255, 0.9);
            box-shadow: 0px 14px 55px 5px rgba(0,0,0,0.1);
            padding: 35px;
            padding-top: 20px;
            border-radius: 2rem;
            min-width: 750px;
            min-height: 400px;
         }
         .logo_container {
            z-index: -1;
            display: block;
            position: fixed;
            top: 120px;
            left: 400px;
         }
         .outer_container {
            width: 100%;
            height: 100%;
            display: flex;
            flex-direction: column;
            align-items: center;
            position: absolute;
            top: 250px;
         }
         .message {
            display: inline-block;
            border-radius: 5px;
            padding: 5px;
            font-weight: bold;
            color: black;
            background-color: lightgray;
         }  
         .footer {
            position: absolute;
            bottom: 0;
            width: 100%;
            text-align: center;
            font-size: 0.8rem;
            color: gray;
            padding: 10px;
         }
    </style>
</head>
