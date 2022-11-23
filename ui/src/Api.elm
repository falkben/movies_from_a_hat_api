module Api exposing (Config, Movie, getConfig, searchMovies)

import Effect exposing (Effect)
import Http exposing (expectJson)
import Json.Decode as Decode exposing (Decoder)
import Url.Builder exposing (QueryParameter, string)


urlBuilder : List String -> List QueryParameter -> String
urlBuilder =
    Url.Builder.crossOrigin "http://localhost:8000"


type alias Config =
    { imgBase : String
    , posterSizes : List String
    }


type alias Movie =
    { title : String
    , posterUrl : String
    }


getConfig : (Result Http.Error Config -> msg) -> Effect msg
getConfig msg =
    Http.get
        { url = "/json/config.json"
        , expect = expectJson msg configDecoder
        }
        |> Effect.fromCmd


searchMovies : String -> (Result Http.Error (List Movie) -> msg) -> Effect msg
searchMovies query msg =
    Http.get
        { url =
            urlBuilder [ "search_movies" ]
                [ string "query" query ]
        , expect = expectJson msg (Decode.list movieDecoder)
        }
        |> Effect.fromCmd



-- DECODERS


configDecoder : Decoder Config
configDecoder =
    Decode.map2 Config
        (Decode.at [ "images", "base_url" ] Decode.string)
        (Decode.at [ "images", "poster_sizes" ] (Decode.list Decode.string))


movieDecoder : Decoder Movie
movieDecoder =
    Decode.map2 Movie
        (Decode.field "title" Decode.string)
        (Decode.field "poster_path" Decode.string
            |> Decode.map (String.append "https://image.tmdb.org/t/p/w500")
        )
