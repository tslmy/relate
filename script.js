userInputCache = new Map()


wikidataSearch = (userInput) => {
  if (userInput in userInputCache) {
    return userInputCache[userInput]
  } else {
    fetch(wdk.searchEntities(userInput)).then(
      (res) => {console.log(res);JSON.parse(res)}).then(
      (res) => {

        if (res.success) {
          result = res.search[0].title
          if (result) {
            userInputCache[res.searchInfo.search] = result
            return result
          } else {
            return ''
          }
        }
      })
  }
}
