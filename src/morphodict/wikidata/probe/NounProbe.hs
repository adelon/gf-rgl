module Main (main) where

import Control.Exception (evaluate)
import Data.Char (ord)
import Data.List (find)
import Numeric (showHex)
import PGF
import System.Environment (getArgs)
import System.Exit (die)
import System.IO


data Request = Request
  { candidateId :: String
  , optionId :: String
  , functionId :: String
  }


manifestHeader :: String
manifestHeader =
  "candidate_id\toption_id\tfunction_id\tconstructor\t" ++
  "explicit_form_arguments\texpression"


outputHeader :: String
outputHeader =
  "candidate_id\toption_id\tfunction_id\tvariant_index\tfield\tvalue_json"


splitTabs :: String -> [String]
splitTabs input =
  case break (== '\t') input of
    (field, []) -> [field]
    (field, _ : rest) -> field : splitTabs rest


parseRequest :: Int -> String -> Either String Request
parseRequest lineNumber input =
  case splitTabs input of
    candidate : option : function : _constructor : _explicit : _expression : []
      | all (not . null) [candidate, option, function] ->
          Right (Request candidate option function)
    _ -> Left ("invalid proposal manifest row " ++ show lineNumber)


readManifest :: FilePath -> IO [Request]
readManifest path = do
  contents <- readUtf8 path
  case lines contents of
    header : rows
      | header == manifestHeader ->
          either die pure (sequence (zipWith parseRequest [2 ..] rows))
      | otherwise -> die "proposal manifest header does not match probe schema"
    [] -> die "proposal manifest is empty"


readUtf8 :: FilePath -> IO String
readUtf8 path = do
  handle <- openFile path ReadMode
  hSetEncoding handle utf8
  contents <- hGetContents handle
  _ <- evaluate (length contents)
  hClose handle
  pure contents


hex4 :: Int -> String
hex4 value = replicate (4 - length digits) '0' ++ digits
  where
    digits = showHex value ""


jsonString :: String -> String
jsonString value = '"' : concatMap escape value ++ "\""
  where
    escape '"' = "\\\""
    escape '\\' = "\\\\"
    escape '\b' = "\\b"
    escape '\f' = "\\f"
    escape '\n' = "\\n"
    escape '\r' = "\\r"
    escape '\t' = "\\t"
    escape character
      | ord character < 0x20 = "\\u" ++ hex4 (ord character)
      | otherwise = [character]


renderRequest :: PGF -> Language -> Request -> [String]
renderRequest pgf language request =
  case tabularLinearizes pgf language expression of
    [] -> [prefix ++ "\t0\t__no_linearization__\tnull"]
    tables ->
      [ prefix ++ "\t" ++ show variantIndex ++ "\t" ++ field ++ "\t" ++
        jsonString value
      | (variantIndex, table) <- zip [(1 :: Int) ..] tables
      , (field, value) <- table
      ]
  where
    prefix = intercalateTabs
      [candidateId request, optionId request, functionId request]
    expression = mkApp (mkCId "probe_record") [mkApp (mkCId (functionId request)) []]


intercalateTabs :: [String] -> String
intercalateTabs [] = ""
intercalateTabs (field : fields) = field ++ concatMap ('\t' :) fields


main :: IO ()
main = do
  hSetEncoding stdout utf8
  hSetEncoding stderr utf8
  arguments <- getArgs
  case arguments of
    [pgfPath, manifestPath] -> do
      pgf <- readPGF pgfPath
      language <- maybe
        (die "PGF does not contain WdnPilotGer")
        pure
        (find (== mkCId "WdnPilotGer") (languages pgf))
      requests <- readManifest manifestPath
      putStrLn outputHeader
      mapM_ putStrLn (concatMap (renderRequest pgf language) requests)
    _ -> die "usage: NounProbe PGF PROPOSAL_MANIFEST"
