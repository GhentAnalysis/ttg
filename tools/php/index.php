<html>
<head>
<title><?php echo str_replace('/eos/user/t/tomc/www','',getcwd()); ?></title>
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
    float: right;
}
div.bar {
    display: block;
    float: left;
    margin: 0.5em 1em 0.2em 1em;
    padding: 10px;
    color: #29407C;
    background: white;
    text-align: center;
    border: 1px solid #29407C;
    border-radius: 5px;
}
a.bar {
    display: block;
    float: left;
    margin: 0.5em 1em 0.2em 1em;
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
div.pic h3 { 
    font-size: 11pt;
    margin: 0.5em 1em 0.2em 1em;
}
div.pic p {
    font-size: 11pt;
    margin: 0.0em 1em 0.2em 1em;
}
div.pic {
    display: block;
    float: left;
    background-color: white;
    border: 1px solid #ccc;
    border-radius: 5px;
    padding: 2px;
    text-align: center;
    margin: 40px 10px 10px 2px;
}
div.picRecent {
    display: block;
    float: left;
    background-color: white;
    border: 1px solid green;
    border-radius: 5px;
    padding: 2px;
    text-align: center;
    margin: 40px 10px 10px 2px;
}
div.picAging {
    display: block;
    float: left;
    background-color: white;
    border: 1px solid orange;
    border-radius: 5px;
    padding: 2px;
    text-align: center;
    margin: 40px 10px 10px 2px;
}
div.picOld {
    display: block;
    float: left;
    background-color: white;
    border: 1px solid green;
    border-radius: 5px;
    padding: 2px;
    text-align: center;
    margin: 40px 10px 10px 2px;
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
a { text-decoration: none; color: #29407C; }
a:hover { text-decoration: underline; color: #D08504; }
</style>
</head>
<body>
<div>
<?php
  function showIfExists($path, $name){
    if(file_exists($path)){
      if(realpath('./')!=realpath($path)){
        $webPath = str_replace('eos/user/t/tomc/www', 'tomc', $path).'/?'.$_SERVER['QUERY_STRING'];
        print "<div><a class=\"bar\" href=\"$webPath\">$name</a></div>";
      } else {
        print "<div><div class=\"bar\">$name</div></div>";
      }
    }
  }
  showIfExists('..', 'parent');

  $fullPath=realpath("./");
  $channels=array('all','ee','emu','mumu','SF','all','noData');
  $myChannel=NULL;
  foreach($channels as $c){
    if(strpos($fullPath, '/'.$c)!==false){
      $myChannel=$c;
    }
  }

  if(!is_null($myChannel)){
    $logPath    =str_replace('/'.$myChannel.'/',     '/'.$myChannel.'-log/', $fullPath);
    $linPath    =str_replace('/'.$myChannel.'-log/', '/'.$myChannel.'/',     $fullPath);
    $eePath     =str_replace('/'.$myChannel,         '/ee',        $fullPath);
    $mumuPath   =str_replace('/'.$myChannel,         '/mumu',      $fullPath);
    $allPath    =str_replace('/'.$myChannel,         '/all',       $fullPath);
    $emuPath    =str_replace('/'.$myChannel,         '/emu',       $fullPath);
    $SFPath     =str_replace('/'.$myChannel,         '/SF',        $fullPath);
    $noDataPath =str_replace('/'.$myChannel,         '/noData',    $fullPath);

    function multipleOptions($options){
      $counter = 0;
      foreach($options as $o){
        if(file_exists($o) and $o!=$fullPath){
          $counter +=1;
        }
      }
      return ($counter > 0);
    }

    if(multipleOptions(array($logPath,$linPath))){
      showIfExists($logPath,   'logarithmic');
      showIfExists($linPath,   'linear');
    }
    if(multipleOptions(array($eePath,$emuPath,$mumuPath,$allPath,$SFPath,$noDataPath))){
      showIfExists($eePath,    'ee');
      showIfExists($emuPath,   'e&#956');
      showIfExists($mumuPath,  '&#956&#956');
      showIfExists($allPath,   'all');
      showIfExists($SFPath,    'SF');
      showIfExists($noDataPath,'no data');
    }
  }
?>
</div>
<h1><form>filter  <input type="text" name="match" size="30" value="<?php if (isset($_GET['match'])) print htmlspecialchars($_GET['match']);  ?>" /><input type="Submit" value="Go" /></form></h1>
<br style="clear:both" />
<div>
<pre style="font-size:80%">
<?php
  if(file_exists('info.txt')){
    echo file_get_contents('info.txt');
  }
?>
</pre>
</div>
<div>
<?php
$displayed = array();
if ($_GET['noplots']) {
    print "Plots will not be displayed.\n";
} else {
  function displayFigures($figExt, $displayed){
    $other_exts = array('.pdf', '.cxx', '.eps', '.root', '.txt', '.tex', '.C');
    $filenames = glob('*.'.$figExt); sort($filenames);
    $files = scandir('*.'.$figExt, SCANDIR_SORT_DESCENDING);
    $newest_file = $files[0];
    foreach ($filenames as $filename) {
        if (isset($_GET['match']) && !fnmatch('*'.$_GET['match'].'*', $filename)) continue;
        if (in_array($filename,$used)) continue;
        array_push($displayed, $filename);
        $name=str_replace('.'.$figExt, '', $filename);
        if      (time()-filemtime($filename)             > 3  *3600)  { print "<div class='pic'>\n"; }
        else if (filemtime($newest)-filemtime($filename) > 5  *3600)  { print "<div class='picAging'>\n"; }
        else if (filemtime($newest)-filemtime($filename) > 240*3600)  { print "<div class='picOld'>\n"; }
        else                                                          { print "<div class='picRecent'>\n"; }
       
        print "<h3><a href=\"$filename\">$name</a></h3>";
        print "<a href=\"$filename\"><img src=\"$filename\" style=\"border: none; width: 300px; \"></a>";
        $others = array();
        foreach ($other_exts as $ex) {
            $exNoDot=str_replace('.','',$ex);
            $other_filename = str_replace('.'.$figExt, $ex, $filename);
            array_push($displayed, $other_filename);
            if(file_exists($other_filename) and filemtime($other_filename)-filemtime($filename)<100){
              array_push($others, "<a class=\"file\" href=\"$other_filename\">[" . $exNoDot . "]</a>");
            }
        }

        $gitInfo = str_replace('.'.$figExt, '.gitInfo', $filename);
        array_push($displayed, $gitInfo);
        if(file_exists($gitInfo) and filemtime($other_filename)-filemtime($filename)<100){
          print "<p style='font-size:80%'>Modified: <a class=\"file\" href=\"$gitInfo\">".date ("F d Y H:i:s", filemtime($filename)) . "</a></p>";
        } else {
          print "<p style='font-size:80%'>Modified: ".date ("F d Y H:i:s", filemtime($filename)) . " </p>";
        }
        if ($others) print "<p>Also as ".implode(', ',$others)."</p>";
        print "</div>";
    }
    return $displayed;
  }
  $displayed = displayFigures('png', $displayed);
  $displayed = displayFigures('jpg', $displayed);
}
?>
</div>
<div class="list">
<ul>
<?
$nondirs = array();
foreach (glob("*") as $filename) {
    if ($_GET['noplots'] || !in_array($filename, $displayed)) {
        if (isset($_GET['match']) && !fnmatch('*'.$_GET['match'].'*', $filename)) continue;
        if (is_dir($filename)) {
            print "<li>[DIR] <a href=\"$filename\">$filename</a></li>";
        } else if ($filename != "index.php" and $filename != "info.txt" and $filename != "git.txt") {
            array_push($nondirs,"<li><a href=\"$filename\">$filename</a></li>");
        }
    }
}
foreach ($nondirs as $file) {
    print $file;
}
?>
</ul>
</div>
<pre style="font-size:50%">
<?php
/*
  if(file_exists('git.txt')){
    print "<h3><a class=\"file\" href=git.txt>gitInfo</a></h3>";
  }
*/
?>
</pre>
</body>
</html>
