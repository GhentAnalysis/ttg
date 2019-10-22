<html>
<head>
<title>
<?php 
  if(basename(__FILE__)=="index.php"){
    $user = get_current_user(); 
    echo str_replace('/eos/user/'.$user[0].'/'.$user.'/www','',getcwd());
  } else {
    // TITLE -- inserted by makeWebpage.py
  }
?>
</title>

<!-- Styles to be used -->
<style type='text/css'>
body {
    font-family: "Helvetica", sans-serif;
    font-size: 9pt;
    line-height: 10.5pt;
}
h1 {
    font-size: 14pt;
    margin: 0.5em 1em 0.2em 1em;
    text-align: left;
    display: inline-block;
}
div.fixed {
    position: fixed;
    white-space: nowrap;
    width:100%;
}
div.bar {
    display: inline-block;
    margin: 0.5em 0.6em 0.2em 0.6em;
    padding: 10px;
    color: #29407C;
    background: white;
    text-align: center;
    border: 1px solid #29407C;
    border-radius: 5px;
}
div.barEmpty {
    color: #ccc;
    border: 1px solid #ccc;
}
a.bar {
    display: inline-block;
    margin: 0.5em 0.6em 0.2em 0.6em;
    padding: 10px;
    color: white;
    background: #29407C;
    text-align: center;
    border: 1px solid #29407C;
    border-radius: 5px;
}
a.bar:hover {
    background-color: #4CAF50;
    color: white;
}
div.list {
    font-size: 13pt;
    margin: 0.5em 1em 1.2em 1em;
    display: block; 
    clear: both;
}
div.list li {
    margin-top: 0.3em;
}
div.list2 li {
    margin-top: 0.3em;
    line-height: 1.3;
}
a { text-decoration: none; color: #29407C; }
a:hover { text-decoration: underline; color: #D08504; }
</style>
</head>

<body>

<!-- Adding some buttons on top -->
<div class="fixed">
<?php
  // If "path" exists, show a button to "path" with text "name"
  function showIfExists($path, $name){
    if(file_exists($path)){
      if(realpath('./')!=realpath($path)){
        $user = get_current_user();
        $webPath = str_replace('user/'.$user[0].'/'.$user.'/www', $user, $path);
        $webPath = str_replace('storage_mnt/storage/user/'.$user.'/public_html', '~'.$user, $path);
        print "<span><a class=\"bar\" href=\"$webPath\">$name</a></span>";
      } else {
        print "<span><div class=\"bar\">$name</div></span>";
      }
    } else {
      print "<span><div class=\"bar barEmpty\">$name</div></span>";
    }
  }
  showIfExists('..', 'parent');
  # SHOWIFEXISTS       - inserted by the makeROC.py
?>
</div>
<br style="clear:both" />

<?php
  // if it is an index.php make a list of available subdirectories or triggers -->
  if(basename(__FILE__)=="index.php"){
    print '<div class="list" style="margin-top: 2cm">';
    print '<ul>';
    $triggers = array();
    foreach (glob("*") as $filename){
      if($filename == "index.php") continue;
      if(isset($_GET['match']) && !fnmatch('*'.$_GET['match'].'*', $filename)) continue;
      if(is_dir($filename) and $filename != 'json'){
        print "<li>[DIR] <a href=\"$filename\">$filename</a></li>";
      } else if (pathinfo($filename, PATHINFO_EXTENSION) == 'php' and $filename != "index.php"){
        $displayname = pathinfo($filename, PATHINFO_FILENAME);
        array_push($triggers,"<li><a href=\"$filename\">$displayname</a></li>");
      }
    }
    foreach ($triggers as $file){print $file;}
    print '</ul>';
    print '</div>';
  }
?>
<br style="clear:both;margin-bottom:4mm" />
<!-- DIV       - inserted by the makeROC.py -->
</body>
</html>
