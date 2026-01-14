/*************************************************************************
 *                                                                       *
 * $Archive:: /Arcus Technology/PerformaxCom/PerformaxCom.h              *
 *                                                                       *
 * $Workfile:: PerformaxCom.h											 *
 *                                                                       *
 * $Revision:: 1                                                         *
 *                                                                       *
 * $Date:: 10/17/04														 *
 *                                                                       *
 * $Author:: CCC		                                                 *
 *                                                                       *
 * Module Description:                                                   *
 *     DLL for the Performax Device										 *
 *     Main Module                                                       *
 *                                                                       *
 * Environment:                                                          *
 *     User mode only                                                    *
 *                                                                       *
 *************************************************************************/

#ifdef PERFORMAXCOM_EXPORTS
#define PERFORMAXCOM_API __declspec(dllexport)
#else
#define PERFORMAXCOM_API __declspec(dllimport)
#endif

extern PERFORMAXCOM_API int nPerformaxCom;

#ifdef __cplusplus
extern "C" {
#endif

PERFORMAXCOM_API int fnPerformaxCom(void);

BOOL PERFORMAXCOM_API _stdcall fnPerformaxComFlush(IN HANDLE pHandle);
BOOL PERFORMAXCOM_API _stdcall fnPerformaxComGetNumDevices(OUT LPDWORD lpNumDevices);
BOOL PERFORMAXCOM_API _stdcall fnPerformaxComGetProductString(IN DWORD dwNumDevices, OUT LPVOID lpDeviceString, IN DWORD dwOptions);
BOOL PERFORMAXCOM_API _stdcall fnPerformaxComOpen(IN DWORD dwDeviceNum, OUT HANDLE* pHandle);
BOOL PERFORMAXCOM_API _stdcall fnPerformaxComClose(IN HANDLE pHandle);
BOOL PERFORMAXCOM_API _stdcall fnPerformaxComSetTimeouts(IN DWORD dwReadTimeout, DWORD dwWriteTimeout);
BOOL PERFORMAXCOM_API _stdcall fnPerformaxComSendRecv(IN HANDLE pHandle, IN LPVOID wBuffer, IN DWORD dwNumBytesToWrite, IN DWORD dwNumBytesToRead, OUT LPVOID rBuffer);


#ifdef __cplusplus
}
#endif
